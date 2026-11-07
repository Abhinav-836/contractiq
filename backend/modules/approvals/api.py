from typing import List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from modules.approvals import service
from modules.notifications.service import Outbox, deliver
from modules.approvals.schemas import ApprovalCreate, ApprovalDecision, ApprovalOut, ApprovalStatsOut
from modules.workspaces.deps import current_workspace
from modules.workspaces.permissions import WorkspaceContext

router = APIRouter()


@router.get("", response_model=List[ApprovalOut])
async def list_approvals(
    scope: Literal["waiting", "requested", "all"] = "all",
    status: Optional[Literal["pending", "approved", "rejected", "cancelled"]] = Query(None),
    ctx: WorkspaceContext = Depends(current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """waiting = requests waiting for your decision; requested = ones you asked for."""
    return await service.list_inbox(db, ctx, scope, status)


@router.get("/stats", response_model=ApprovalStatsOut)
async def approval_stats(ctx: WorkspaceContext = Depends(current_workspace), db: AsyncSession = Depends(get_db)):
    return await service.stats(db, ctx)


@router.get("/contract/{contract_id}", response_model=List[ApprovalOut])
async def contract_approvals(
    contract_id: str, ctx: WorkspaceContext = Depends(current_workspace), db: AsyncSession = Depends(get_db)
):
    """Every approval request for a contract, newest first."""
    return await service.list_for_contract(db, ctx, contract_id)


@router.post("/contract/{contract_id}", response_model=ApprovalOut, status_code=201)
async def request_approval(
    contract_id: str,
    body: ApprovalCreate,
    background: BackgroundTasks,
    ctx: WorkspaceContext = Depends(current_workspace),
    db: AsyncSession = Depends(get_db),
):
    outbox = Outbox()
    out = await service.create_request(db, ctx, contract_id, body.reviewer_ids, body.note, outbox)
    if outbox:
        await db.commit()  # emails refer to these rows; save them before the background send
        background.add_task(deliver, outbox)
    return out


@router.post("/{request_id}/decision", response_model=ApprovalOut)
async def decide(
    request_id: str,
    body: ApprovalDecision,
    background: BackgroundTasks,
    ctx: WorkspaceContext = Depends(current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Reviewers of any role (including viewers) can decide."""
    outbox = Outbox()
    out = await service.decide(db, ctx, request_id, body.decision, body.comment, outbox)
    if outbox:
        await db.commit()  # emails refer to these rows; save them before the background send
        background.add_task(deliver, outbox)
    return out


@router.post("/{request_id}/cancel", response_model=ApprovalOut)
async def cancel(request_id: str, ctx: WorkspaceContext = Depends(current_workspace), db: AsyncSession = Depends(get_db)):
    return await service.cancel(db, ctx, request_id)
