import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import gen_uuid
from modules.contracts.models import Contract
from modules.users.models import User
from modules.workspaces.models import Workspace, WorkspaceInvite, WorkspaceMember
from modules.workspaces.permissions import WorkspaceContext, can_grant, can_manage

NOT_FOUND = "Workspace not found"
INVITE_UNAVAILABLE = "This invite link is invalid, expired or has been used up."


def personal_workspace_name(user_name: str) -> str:
    name = (user_name or "").strip() or "My"
    return f"{name}'s workspace"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """SQLite returns naive datetimes; treat them as UTC."""
    if dt is None or dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


def invite_is_usable(invite: WorkspaceInvite) -> bool:
    if invite.revoked_at is not None:
        return False
    if as_aware(invite.expires_at) <= utcnow():
        return False
    return invite.max_uses is None or invite.use_count < invite.max_uses


async def create_personal_workspace(db: AsyncSession, user: User) -> Workspace:
    workspace = Workspace(
        id=gen_uuid(), name=personal_workspace_name(user.name), is_personal=True, created_by=user.id
    )
    db.add(workspace)
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    await db.flush()
    return workspace


async def get_membership(db: AsyncSession, workspace_id: str, user_id: str) -> Optional[WorkspaceMember]:
    return (
        await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id
            )
        )
    ).scalar_one_or_none()


async def context_for(db: AsyncSession, workspace_id: str, user_id: str) -> WorkspaceContext:
    """404 (not 403) for workspaces the user isn't in, so ids can't be probed."""
    membership = await get_membership(db, workspace_id, user_id)
    if not membership:
        raise HTTPException(404, NOT_FOUND)
    return WorkspaceContext(user_id=user_id, workspace_id=workspace_id, role=membership.role)


async def default_context(db: AsyncSession, user_id: str) -> WorkspaceContext:
    """The user's personal workspace — or, failing that, their oldest membership."""
    row = (
        await db.execute(
            select(WorkspaceMember.workspace_id, WorkspaceMember.role)
            .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(
                (and_(Workspace.is_personal.is_(True), WorkspaceMember.role == "owner")).desc(),
                WorkspaceMember.created_at,
            )
            .limit(1)
        )
    ).first()
    if row:
        return WorkspaceContext(user_id=user_id, workspace_id=row.workspace_id, role=row.role)

    # Safety net: an account with no workspace at all gets its personal one now.
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(401, "User not found")
    workspace = await create_personal_workspace(db, user)
    await db.commit()
    return WorkspaceContext(user_id=user_id, workspace_id=workspace.id, role="owner")


# ─────────────────────────────────────────────────────────────────────────────
# Workspaces
# ─────────────────────────────────────────────────────────────────────────────

async def list_for_user(db: AsyncSession, user_id: str) -> list[dict]:
    member_count = (
        select(func.count())
        .select_from(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == Workspace.id)
        .correlate(Workspace)
        .scalar_subquery()
    )
    contract_count = (
        select(func.count())
        .select_from(Contract)
        .where(Contract.workspace_id == Workspace.id)
        .correlate(Workspace)
        .scalar_subquery()
    )
    rows = (
        await db.execute(
            select(Workspace, WorkspaceMember.role, member_count, contract_count)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.is_personal.desc(), Workspace.name)
        )
    ).all()
    return [
        {
            "id": ws.id,
            "name": ws.name,
            "is_personal": ws.is_personal,
            "role": role,
            "member_count": members,
            "contract_count": contracts,
            "created_at": ws.created_at,
        }
        for ws, role, members, contracts in rows
    ]


async def create_workspace(db: AsyncSession, user_id: str, name: str) -> dict:
    workspace = Workspace(id=gen_uuid(), name=name, is_personal=False, created_by=user_id)
    db.add(workspace)
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user_id, role="owner"))
    await db.commit()
    return {
        "id": workspace.id,
        "name": name,
        "is_personal": False,
        "role": "owner",
        "member_count": 1,
        "contract_count": 0,
        "created_at": workspace.created_at,
    }


async def rename_workspace(db: AsyncSession, ctx: WorkspaceContext, name: str) -> None:
    ctx.require("admin", "Only owners and admins can rename the workspace")
    await db.execute(update(Workspace).where(Workspace.id == ctx.workspace_id).values(name=name))
    await db.commit()


async def delete_workspace(db: AsyncSession, ctx: WorkspaceContext) -> None:
    ctx.require("owner", "Only the owner can delete the workspace")
    workspace = await db.get(Workspace, ctx.workspace_id)
    if workspace.is_personal:
        raise HTTPException(400, "Your personal workspace can't be deleted")
    contracts = (
        await db.execute(select(func.count()).select_from(Contract).where(Contract.workspace_id == workspace.id))
    ).scalar()
    if contracts:
        raise HTTPException(
            409, f"Delete the {contracts} contract{'s' if contracts != 1 else ''} in this workspace first"
        )
    await db.delete(workspace)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Members
# ─────────────────────────────────────────────────────────────────────────────

async def list_members(db: AsyncSession, ctx: WorkspaceContext) -> list[dict]:
    rows = (
        await db.execute(
            select(WorkspaceMember, User.name, User.email)
            .join(User, User.id == WorkspaceMember.user_id)
            .where(WorkspaceMember.workspace_id == ctx.workspace_id)
        )
    ).all()
    members = [
        {
            "user_id": m.user_id,
            "name": name,
            "email": email,
            "role": m.role,
            "joined_at": m.created_at,
            "is_you": m.user_id == ctx.user_id,
        }
        for m, name, email in rows
    ]
    order = {"owner": 0, "admin": 1, "member": 2, "viewer": 3}
    return sorted(members, key=lambda m: (order.get(m["role"], 9), (m["name"] or "").lower()))


async def change_role(db: AsyncSession, ctx: WorkspaceContext, target_user_id: str, new_role: str) -> None:
    target = await get_membership(db, ctx.workspace_id, target_user_id)
    if not target:
        raise HTTPException(404, "Member not found")
    if target.role == new_role:
        return
    if not (can_manage(ctx.role, target.role) and can_grant(ctx.role, new_role)):
        raise HTTPException(403, "You don't have permission to make that change")
    target.role = new_role
    await db.commit()


async def remove_member(db: AsyncSession, ctx: WorkspaceContext, target_user_id: str) -> None:
    target = await get_membership(db, ctx.workspace_id, target_user_id)
    if not target:
        raise HTTPException(404, "Member not found")
    if target_user_id == ctx.user_id:
        if target.role == "owner":
            raise HTTPException(400, "Owners can't leave their own workspace")
    elif not can_manage(ctx.role, target.role):
        raise HTTPException(403, "You don't have permission to remove this member")
    from modules.approvals.service import on_member_removed

    await on_member_removed(db, ctx.workspace_id, target_user_id)
    await db.delete(target)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Invites
# ─────────────────────────────────────────────────────────────────────────────

def _invite_out(invite: WorkspaceInvite, inviter_name: Optional[str] = None) -> dict:
    return {
        "id": invite.id,
        "role": invite.role,
        "expires_at": as_aware(invite.expires_at),
        "max_uses": invite.max_uses,
        "use_count": invite.use_count,
        "created_at": as_aware(invite.created_at),
        "created_by_name": inviter_name,
    }


async def list_invites(db: AsyncSession, ctx: WorkspaceContext) -> list[dict]:
    ctx.require("admin", "Only owners and admins can see invite links")
    rows = (
        await db.execute(
            select(WorkspaceInvite, User.name)
            .outerjoin(User, User.id == WorkspaceInvite.created_by)
            .where(WorkspaceInvite.workspace_id == ctx.workspace_id)
            .order_by(WorkspaceInvite.created_at.desc())
        )
    ).all()
    return [_invite_out(inv, name) for inv, name in rows if invite_is_usable(inv)]


async def create_invite(
    db: AsyncSession, ctx: WorkspaceContext, role: str, expires_in_days: int, max_uses: Optional[int]
) -> dict:
    ctx.require("admin", "Only owners and admins can invite people")
    if not can_grant(ctx.role, role):
        raise HTTPException(403, "Only the owner can invite admins")
    token = secrets.token_urlsafe(32)
    invite = WorkspaceInvite(
        id=gen_uuid(),
        workspace_id=ctx.workspace_id,
        token_hash=hash_token(token),
        role=role,
        created_by=ctx.user_id,
        expires_at=utcnow() + timedelta(days=expires_in_days),
        max_uses=max_uses,
        use_count=0,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return {**_invite_out(invite), "token": token}


async def revoke_invite(db: AsyncSession, ctx: WorkspaceContext, invite_id: str) -> None:
    ctx.require("admin", "Only owners and admins can revoke invite links")
    result = await db.execute(
        update(WorkspaceInvite)
        .where(
            WorkspaceInvite.id == invite_id,
            WorkspaceInvite.workspace_id == ctx.workspace_id,
            WorkspaceInvite.revoked_at.is_(None),
        )
        .values(revoked_at=utcnow())
    )
    if not result.rowcount:
        raise HTTPException(404, "Invite not found")
    await db.commit()


async def _invite_by_token(db: AsyncSession, token: str) -> WorkspaceInvite:
    invite = (
        await db.execute(select(WorkspaceInvite).where(WorkspaceInvite.token_hash == hash_token(token)))
    ).scalar_one_or_none()
    if not invite or not invite_is_usable(invite):
        raise HTTPException(404, INVITE_UNAVAILABLE)
    return invite


async def preview_invite(db: AsyncSession, token: str) -> dict:
    invite = await _invite_by_token(db, token)
    workspace = await db.get(Workspace, invite.workspace_id)
    inviter = await db.get(User, invite.created_by) if invite.created_by else None
    return {
        "workspace_name": workspace.name,
        "role": invite.role,
        "invited_by": inviter.name if inviter else None,
        "expires_at": as_aware(invite.expires_at),
    }


async def accept_invite(db: AsyncSession, token: str, user_id: str) -> dict:
    invite = await _invite_by_token(db, token)
    existing = await get_membership(db, invite.workspace_id, user_id)
    if existing:
        # Never change an existing member's role through a link (it could be a downgrade).
        return {"workspace_id": invite.workspace_id, "role": existing.role, "already_member": True}

    # Claim one use atomically, so two people can't both take the last use.
    claimed = await db.execute(
        update(WorkspaceInvite)
        .where(
            WorkspaceInvite.id == invite.id,
            WorkspaceInvite.revoked_at.is_(None),
            or_(WorkspaceInvite.max_uses.is_(None), WorkspaceInvite.use_count < WorkspaceInvite.max_uses),
        )
        .values(use_count=WorkspaceInvite.use_count + 1)
    )
    if not claimed.rowcount:
        raise HTTPException(404, INVITE_UNAVAILABLE)
    db.add(WorkspaceMember(workspace_id=invite.workspace_id, user_id=user_id, role=invite.role))
    await db.commit()
    return {"workspace_id": invite.workspace_id, "role": invite.role, "already_member": False}

