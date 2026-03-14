from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from core.dependencies import get_db
from core.security import get_current_user_id
from .models import Alert
from .schemas import AlertOut, AlertCreate, AlertUpdate
from typing import List, Optional

router = APIRouter()


@router.get("", response_model=List[AlertOut])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """List alerts with filters"""
    query = select(Alert).order_by(Alert.created_at.desc())
    
    if unread_only:
        query = query.where(Alert.read == False)
    if type:
        query = query.where(Alert.type == type)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_alert_stats(db: AsyncSession = Depends(get_db)):
    """Get alert statistics"""
    total = await db.execute(select(Alert))
    total_count = len(total.scalars().all())
    
    unread = await db.execute(select(Alert).where(Alert.read == False))
    unread_count = len(unread.scalars().all())
    
    return {
        "total": total_count,
        "unread": unread_count,
    }


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark alert as read"""
    await db.execute(
        update(Alert)
        .where(Alert.id == alert_id)
        .values(read=True)
    )
    await db.commit()
    return {"status": "read", "id": alert_id}


@router.post("/mark-all-read")
async def mark_all_alerts_read(
    db: AsyncSession = Depends(get_db),
):
    """Mark all alerts as read"""
    await db.execute(update(Alert).values(read=True))
    await db.commit()
    return {"status": "all alerts marked as read"}


@router.delete("/{alert_id}")
async def dismiss_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an alert"""
    await db.execute(delete(Alert).where(Alert.id == alert_id))
    await db.commit()
    return {"status": "dismissed", "id": alert_id}