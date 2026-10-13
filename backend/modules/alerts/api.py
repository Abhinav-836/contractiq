from typing import Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import require_auth
from .models import Alert
from .schemas import AlertOut

router = APIRouter()


@router.get("", response_model=List[AlertOut])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
    unread_only: bool = False,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    q = select(Alert).order_by(Alert.created_at.desc())
    if unread_only:
        q = q.where(Alert.read.is_(False))
    if type:
        q = q.where(Alert.type == type)
    q = q.offset(skip).limit(limit)
    return list((await db.execute(q)).scalars().all())


@router.get("/stats")
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    total = (await db.execute(select(func.count(Alert.id)))).scalar() or 0
    unread = (
        await db.execute(select(func.count(Alert.id)).where(Alert.read.is_(False)))
    ).scalar() or 0
    return {"total": total, "unread": unread}


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    await db.execute(update(Alert).where(Alert.id == alert_id).values(read=True))
    await db.commit()
    return {"status": "read", "id": alert_id}


@router.post("/mark-all-read")
async def mark_all_alerts_read(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    await db.execute(update(Alert).values(read=True))
    await db.commit()
    return {"status": "all alerts marked as read"}


@router.delete("/{alert_id}")
async def dismiss_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    await db.execute(delete(Alert).where(Alert.id == alert_id))
    await db.commit()
    return {"status": "dismissed", "id": alert_id}