from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from modules.contracts.repository import workspace_contract_ids
from modules.workspaces.deps import current_workspace, editable_workspace
from modules.workspaces.permissions import WorkspaceContext
from .models import Alert
from .schemas import AlertOut, AlertStatsOut

router = APIRouter()


def _mine(workspace_id: str):
    """Every query is restricted to alerts on the active workspace's contracts."""
    return Alert.contract_id.in_(workspace_contract_ids(workspace_id))


async def _ensure_owned(db: AsyncSession, alert_id: str, workspace_id: str):
    found = (
        await db.execute(select(Alert.id).where(Alert.id == alert_id, _mine(workspace_id)))
    ).scalar_one_or_none()
    if not found:
        raise HTTPException(404, "Alert not found")


@router.get("", response_model=List[AlertOut])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    ctx: WorkspaceContext = Depends(current_workspace),
    unread_only: bool = False,
    type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    q = select(Alert).where(_mine(ctx.workspace_id)).order_by(Alert.created_at.desc())
    if unread_only:
        q = q.where(Alert.read.is_(False))
    if type:
        q = q.where(Alert.type == type)
    q = q.offset(skip).limit(limit)
    return list((await db.execute(q)).scalars().all())


@router.get("/stats", response_model=AlertStatsOut)
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    ctx: WorkspaceContext = Depends(current_workspace),
):
    total = (await db.execute(select(func.count(Alert.id)).where(_mine(ctx.workspace_id)))).scalar() or 0
    unread = (
        await db.execute(
            select(func.count(Alert.id)).where(_mine(ctx.workspace_id), Alert.read.is_(False))
        )
    ).scalar() or 0
    return {"total": total, "unread": unread}


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    ctx: WorkspaceContext = Depends(editable_workspace),
):
    await _ensure_owned(db, alert_id, ctx.workspace_id)
    await db.execute(update(Alert).where(Alert.id == alert_id).values(read=True))
    await db.commit()
    return {"status": "read", "id": alert_id}


@router.post("/mark-all-read")
async def mark_all_alerts_read(
    db: AsyncSession = Depends(get_db),
    ctx: WorkspaceContext = Depends(editable_workspace),
):
    # previously `update(Alert).values(read=True)` — marked EVERY user's alerts read
    await db.execute(
        update(Alert)
        .where(_mine(ctx.workspace_id), Alert.read.is_(False))
        .values(read=True)
        .execution_options(synchronize_session=False)
    )
    await db.commit()
    return {"status": "all alerts marked as read"}


@router.delete("/{alert_id}")
async def dismiss_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    ctx: WorkspaceContext = Depends(editable_workspace),
):
    await _ensure_owned(db, alert_id, ctx.workspace_id)
    await db.execute(delete(Alert).where(Alert.id == alert_id))
    await db.commit()
    return {"status": "dismissed", "id": alert_id}