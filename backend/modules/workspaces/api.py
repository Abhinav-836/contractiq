from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import require_auth
from modules.notifications.service import Outbox, deliver
from modules.workspaces import service
from modules.workspaces.deps import workspace_from_path
from modules.workspaces.permissions import WorkspaceContext
from modules.workspaces.schemas import (
    InviteAccepted,
    InviteCreate,
    InviteCreated,
    InviteOut,
    InvitePreview,
    MemberOut,
    RoleUpdate,
    WorkspaceCreate,
    WorkspaceOut,
    WorkspaceRename,
)

router = APIRouter()
invites_router = APIRouter()


# ── Workspaces ───────────────────────────────────────────────────────────────

@router.get("", response_model=List[WorkspaceOut])
async def list_workspaces(user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    workspaces = await service.list_for_user(db, user_id)
    if not workspaces:
        await service.default_context(db, user_id)  # creates the personal workspace
        workspaces = await service.list_for_user(db, user_id)
    return workspaces


@router.post("", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    body: WorkspaceCreate, user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)
):
    return await service.create_workspace(db, user_id, body.name)


@router.patch("/{workspace_id}")
async def rename_workspace(
    body: WorkspaceRename,
    ctx: WorkspaceContext = Depends(workspace_from_path),
    db: AsyncSession = Depends(get_db),
):
    await service.rename_workspace(db, ctx, body.name)
    return {"id": ctx.workspace_id, "name": body.name}


@router.delete("/{workspace_id}")
async def delete_workspace(
    ctx: WorkspaceContext = Depends(workspace_from_path), db: AsyncSession = Depends(get_db)
):
    await service.delete_workspace(db, ctx)
    return {"message": "Workspace deleted"}


# ── Members ──────────────────────────────────────────────────────────────────

@router.get("/{workspace_id}/members", response_model=List[MemberOut])
async def list_members(
    ctx: WorkspaceContext = Depends(workspace_from_path), db: AsyncSession = Depends(get_db)
):
    return await service.list_members(db, ctx)


@router.patch("/{workspace_id}/members/{user_id}")
async def change_member_role(
    user_id: str,
    body: RoleUpdate,
    ctx: WorkspaceContext = Depends(workspace_from_path),
    db: AsyncSession = Depends(get_db),
):
    await service.change_role(db, ctx, user_id, body.role)
    return {"user_id": user_id, "role": body.role}


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    user_id: str,
    ctx: WorkspaceContext = Depends(workspace_from_path),
    db: AsyncSession = Depends(get_db),
):
    """Remove someone, or leave (user_id = yourself)."""
    await service.remove_member(db, ctx, user_id)
    return {"message": "Left the workspace" if user_id == ctx.user_id else "Member removed"}


# ── Invite links (managing) ──────────────────────────────────────────────────

@router.get("/{workspace_id}/invites", response_model=List[InviteOut])
async def list_invites(
    ctx: WorkspaceContext = Depends(workspace_from_path), db: AsyncSession = Depends(get_db)
):
    return await service.list_invites(db, ctx)


@router.post("/{workspace_id}/invites", response_model=InviteCreated, status_code=201)
async def create_invite(
    body: InviteCreate,
    background: BackgroundTasks,
    ctx: WorkspaceContext = Depends(workspace_from_path),
    db: AsyncSession = Depends(get_db),
):
    outbox = Outbox() if body.email else None
    out = await service.create_invite(db, ctx, body.role, body.expires_in_days, body.max_uses, body.email, outbox)
    if outbox:  # create_invite has already committed
        background.add_task(deliver, outbox)
    return out


@router.delete("/{workspace_id}/invites/{invite_id}")
async def revoke_invite(
    invite_id: str,
    ctx: WorkspaceContext = Depends(workspace_from_path),
    db: AsyncSession = Depends(get_db),
):
    await service.revoke_invite(db, ctx, invite_id)
    return {"message": "Invite link revoked"}


# ── Invite links (joining) ───────────────────────────────────────────────────

@invites_router.get("/{token}", response_model=InvitePreview)
async def preview_invite(token: str, db: AsyncSession = Depends(get_db)):
    """Public: lets the invite page show the workspace name before sign-in."""
    return await service.preview_invite(db, token)


@invites_router.post("/{token}/accept", response_model=InviteAccepted)
async def accept_invite(token: str, user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    return await service.accept_invite(db, token, user_id)
