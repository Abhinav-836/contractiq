"""
Approval workflow.

  * Members and above can ask named reviewers to approve a reviewed contract.
  * Reviewers can be anyone in the workspace except the requester — including
    viewers, so e.g. finance can sign off without being able to edit.
  * Every reviewer must approve; one rejection (with a comment) rejects it.
  * One open request per contract. The requester or an admin can cancel it.
  * contracts.approval_status mirrors the latest request that wasn't cancelled.
"""
from datetime import datetime, timezone
from typing import Iterable, Optional

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import gen_uuid
from modules.approvals.models import ApprovalRequest, ApprovalReviewer
from modules.contracts.models import Contract
from modules.users.models import User
from modules.workspaces.models import WorkspaceMember
from modules.workspaces.permissions import WorkspaceContext

MAX_REVIEWERS = 10
NOT_FOUND = "Approval request not found"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Reading
# ─────────────────────────────────────────────────────────────────────────────

async def _serialize(db: AsyncSession, requests: list[ApprovalRequest], viewer_id: str) -> list[dict]:
    if not requests:
        return []
    ids = [r.id for r in requests]
    reviewers = (
        await db.execute(select(ApprovalReviewer).where(ApprovalReviewer.request_id.in_(ids)))
    ).scalars().all()
    user_ids = {r.requested_by for r in requests} | {r.closed_by for r in requests} | {v.user_id for v in reviewers}
    user_ids.discard(None)
    users = {
        u.id: u
        for u in (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
    } if user_ids else {}
    contracts = {
        c.id: c.filename
        for c in (
            await db.execute(select(Contract.id, Contract.filename).where(Contract.id.in_({r.contract_id for r in requests})))
        ).all()
    }
    name = lambda uid: users[uid].name if uid in users else None  # noqa: E731

    by_request: dict[str, list] = {}
    for v in reviewers:
        by_request.setdefault(v.request_id, []).append(
            {
                "user_id": v.user_id,
                "name": name(v.user_id) or "Former member",
                "decision": v.decision,
                "comment": v.comment,
                "decided_at": v.decided_at,
            }
        )

    out = []
    for r in requests:
        revs = sorted(by_request.get(r.id, []), key=lambda x: (x["name"] or "").lower())
        mine = next((v for v in revs if v["user_id"] == viewer_id), None)
        out.append(
            {
                "id": r.id,
                "contract_id": r.contract_id,
                "contract_filename": contracts.get(r.contract_id),
                "status": r.status,
                "note": r.note,
                "requested_by": r.requested_by,
                "requested_by_name": name(r.requested_by) or "Former member",
                "created_at": r.created_at,
                "closed_at": r.closed_at,
                "closed_by_name": name(r.closed_by),
                "reviewers": revs,
                "approved_count": sum(1 for v in revs if v["decision"] == "approved"),
                "awaiting_my_decision": r.status == "pending" and mine is not None and mine["decision"] is None,
            }
        )
    return out


async def _contract_in_workspace(db: AsyncSession, ctx: WorkspaceContext, contract_id: str) -> Contract:
    contract = await db.get(Contract, contract_id)
    if not contract or contract.workspace_id != ctx.workspace_id:
        raise HTTPException(404, "Contract not found")
    return contract


async def _request_in_workspace(db: AsyncSession, ctx: WorkspaceContext, request_id: str, lock: bool = False) -> ApprovalRequest:
    q = select(ApprovalRequest).where(
        ApprovalRequest.id == request_id, ApprovalRequest.workspace_id == ctx.workspace_id
    )
    if lock:
        # Two reviewers deciding at the same moment must not both miss that
        # the request is now complete. (No-op on SQLite.)
        q = q.with_for_update()
    request = (await db.execute(q)).scalar_one_or_none()
    if not request:
        raise HTTPException(404, NOT_FOUND)
    return request


async def list_for_contract(db: AsyncSession, ctx: WorkspaceContext, contract_id: str) -> list[dict]:
    await _contract_in_workspace(db, ctx, contract_id)
    requests = (
        await db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.contract_id == contract_id)
            .order_by(ApprovalRequest.created_at.desc())
        )
    ).scalars().all()
    return await _serialize(db, list(requests), ctx.user_id)


async def list_inbox(db: AsyncSession, ctx: WorkspaceContext, scope: str, status: Optional[str]) -> list[dict]:
    q = select(ApprovalRequest).where(ApprovalRequest.workspace_id == ctx.workspace_id)
    if scope == "waiting":
        q = q.join(ApprovalReviewer, ApprovalReviewer.request_id == ApprovalRequest.id).where(
            ApprovalReviewer.user_id == ctx.user_id,
            ApprovalReviewer.decision.is_(None),
            ApprovalRequest.status == "pending",
        )
    elif scope == "requested":
        q = q.where(ApprovalRequest.requested_by == ctx.user_id)
    if status:
        q = q.where(ApprovalRequest.status == status)
    requests = (await db.execute(q.order_by(ApprovalRequest.created_at.desc()).limit(200))).scalars().all()
    return await _serialize(db, list(requests), ctx.user_id)


async def stats(db: AsyncSession, ctx: WorkspaceContext) -> dict:
    waiting = await list_inbox(db, ctx, "waiting", None)
    pending = (
        await db.execute(
            select(ApprovalRequest.id).where(
                ApprovalRequest.workspace_id == ctx.workspace_id, ApprovalRequest.status == "pending"
            )
        )
    ).all()
    return {"waiting_for_me": len(waiting), "pending": len(pending)}


# ─────────────────────────────────────────────────────────────────────────────
# Changing
# ─────────────────────────────────────────────────────────────────────────────

async def _sync_contract_status(db: AsyncSession, contract_id: str) -> None:
    """contracts.approval_status = status of the newest request that wasn't cancelled."""
    latest = (
        await db.execute(
            select(ApprovalRequest.status)
            .where(ApprovalRequest.contract_id == contract_id, ApprovalRequest.status != "cancelled")
            .order_by(ApprovalRequest.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    await db.execute(update(Contract).where(Contract.id == contract_id).values(approval_status=latest))


async def _settle(db: AsyncSession, request: ApprovalRequest, closed_by: Optional[str]) -> None:
    """Close the request if a reviewer rejected or everyone approved."""
    decisions = (
        await db.execute(select(ApprovalReviewer.decision).where(ApprovalReviewer.request_id == request.id))
    ).scalars().all()
    if not decisions:
        request.status, request.closed_at, request.closed_by = "cancelled", utcnow(), None
    elif "rejected" in decisions:
        request.status, request.closed_at, request.closed_by = "rejected", utcnow(), closed_by
    elif all(d == "approved" for d in decisions):
        request.status, request.closed_at, request.closed_by = "approved", utcnow(), closed_by
    await db.flush()
    await _sync_contract_status(db, request.contract_id)


async def create_request(
    db: AsyncSession, ctx: WorkspaceContext, contract_id: str, reviewer_ids: Iterable[str], note: Optional[str]
) -> dict:
    ctx.require("member", "You have view-only access to this workspace")
    contract = await _contract_in_workspace(db, ctx, contract_id)
    if contract.status != "completed":
        raise HTTPException(409, "Wait for the review to finish before asking for approval")

    open_request = (
        await db.execute(
            select(ApprovalRequest.id).where(
                ApprovalRequest.contract_id == contract_id, ApprovalRequest.status == "pending"
            )
        )
    ).scalar_one_or_none()
    if open_request:
        raise HTTPException(409, "This contract already has an open approval request")

    reviewer_ids = list(dict.fromkeys(r for r in reviewer_ids if r))
    if not reviewer_ids:
        raise HTTPException(422, "Pick at least one reviewer")
    if len(reviewer_ids) > MAX_REVIEWERS:
        raise HTTPException(422, f"Pick at most {MAX_REVIEWERS} reviewers")
    if ctx.user_id in reviewer_ids:
        raise HTTPException(422, "You can't review your own request")
    members = set(
        (
            await db.execute(
                select(WorkspaceMember.user_id).where(
                    WorkspaceMember.workspace_id == ctx.workspace_id,
                    WorkspaceMember.user_id.in_(reviewer_ids),
                )
            )
        ).scalars().all()
    )
    if len(members) != len(reviewer_ids):
        raise HTTPException(422, "Every reviewer must be in this workspace")

    request = ApprovalRequest(
        id=gen_uuid(),
        contract_id=contract_id,
        workspace_id=ctx.workspace_id,
        requested_by=ctx.user_id,
        note=(note or "").strip() or None,
        status="pending",
        created_at=utcnow(),
    )
    db.add(request)
    await db.flush()
    db.add_all([ApprovalReviewer(request_id=request.id, user_id=uid) for uid in reviewer_ids])
    await db.flush()
    await _sync_contract_status(db, contract_id)
    await db.commit()
    return (await _serialize(db, [request], ctx.user_id))[0]


async def decide(db: AsyncSession, ctx: WorkspaceContext, request_id: str, decision: str, comment: Optional[str]) -> dict:
    request = await _request_in_workspace(db, ctx, request_id, lock=True)
    if request.status != "pending":
        raise HTTPException(409, f"This request was already {request.status}")
    reviewer = await db.get(ApprovalReviewer, (request.id, ctx.user_id))
    if not reviewer:
        raise HTTPException(403, "You're not a reviewer on this request")
    if reviewer.decision is not None:
        raise HTTPException(409, f"You already {reviewer.decision} this request")
    comment = (comment or "").strip() or None
    if decision == "rejected" and not comment:
        raise HTTPException(422, "Say why you're rejecting it, so the requester knows what to change")

    reviewer.decision, reviewer.comment, reviewer.decided_at = decision, comment, utcnow()
    await db.flush()
    await _settle(db, request, closed_by=ctx.user_id)
    await db.commit()
    return (await _serialize(db, [request], ctx.user_id))[0]


async def cancel(db: AsyncSession, ctx: WorkspaceContext, request_id: str) -> dict:
    request = await _request_in_workspace(db, ctx, request_id, lock=True)
    if request.status != "pending":
        raise HTTPException(409, f"This request was already {request.status}")
    if request.requested_by != ctx.user_id and not ctx.can("admin"):
        raise HTTPException(403, "Only the person who asked, or an admin, can cancel this request")
    request.status, request.closed_at, request.closed_by = "cancelled", utcnow(), ctx.user_id
    await db.flush()
    await _sync_contract_status(db, request.contract_id)
    await db.commit()
    return (await _serialize(db, [request], ctx.user_id))[0]


# ─────────────────────────────────────────────────────────────────────────────
# Hooks from other modules (no commit — the caller commits)
# ─────────────────────────────────────────────────────────────────────────────

async def on_member_removed(db: AsyncSession, workspace_id: str, user_id: str) -> None:
    """
    Someone left or was removed: drop them from open requests where they
    hadn't decided yet, so those requests can still finish.
    """
    open_requests = (
        await db.execute(
            select(ApprovalRequest)
            .join(ApprovalReviewer, ApprovalReviewer.request_id == ApprovalRequest.id)
            .where(
                ApprovalRequest.workspace_id == workspace_id,
                ApprovalRequest.status == "pending",
                ApprovalReviewer.user_id == user_id,
                ApprovalReviewer.decision.is_(None),
            )
        )
    ).scalars().all()
    for request in open_requests:
        await db.execute(
            delete(ApprovalReviewer).where(
                ApprovalReviewer.request_id == request.id, ApprovalReviewer.user_id == user_id
            )
        )
        await db.flush()
        await _settle(db, request, closed_by=None)


async def delete_for_contract(db: AsyncSession, contract_id: str) -> None:
    """Explicit cleanup (SQLite doesn't enforce ON DELETE CASCADE)."""
    request_ids = select(ApprovalRequest.id).where(ApprovalRequest.contract_id == contract_id)
    await db.execute(delete(ApprovalReviewer).where(ApprovalReviewer.request_id.in_(request_ids)))
    await db.execute(delete(ApprovalRequest).where(ApprovalRequest.contract_id == contract_id))
