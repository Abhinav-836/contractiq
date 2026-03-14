from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from core.dependencies import get_db
from core.security import get_current_user_id
from .models import Obligation
from .schemas import ObligationOut, ObligationCreate, ObligationUpdate
from typing import List, Optional
from datetime import datetime

router = APIRouter()


@router.get("", response_model=List[ObligationOut])
async def list_obligations(
    db: AsyncSession = Depends(get_db),
    contract_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """List obligations with filters"""
    query = select(Obligation).order_by(Obligation.created_at.desc())
    
    if contract_id:
        query = query.where(Obligation.contract_id == contract_id)
    if status:
        query = query.where(Obligation.status == status)
    if priority:
        query = query.where(Obligation.priority == priority)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_obligation_stats(db: AsyncSession = Depends(get_db)):
    """Get obligation statistics"""
    total = await db.execute(select(Obligation))
    total_count = len(total.scalars().all())
    
    overdue = await db.execute(
        select(Obligation).where(
            Obligation.status == "pending",
            Obligation.due_date < datetime.now().isoformat()
        )
    )
    overdue_count = len(overdue.scalars().all())
    
    pending = await db.execute(
        select(Obligation).where(Obligation.status == "pending")
    )
    pending_count = len(pending.scalars().all())
    
    completed = await db.execute(
        select(Obligation).where(Obligation.status == "completed")
    )
    completed_count = len(completed.scalars().all())
    
    return {
        "total": total_count,
        "overdue": overdue_count,
        "pending": pending_count,
        "completed": completed_count,
    }


@router.get("/{obligation_id}", response_model=ObligationOut)
async def get_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get obligation by ID"""
    result = await db.execute(
        select(Obligation).where(Obligation.id == obligation_id)
    )
    obligation = result.scalar_one_or_none()
    if not obligation:
        raise HTTPException(404, "Obligation not found")
    return obligation


@router.patch("/{obligation_id}/complete")
async def complete_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark obligation as completed"""
    await db.execute(
        update(Obligation)
        .where(Obligation.id == obligation_id)
        .values(status="completed")
    )
    await db.commit()
    return {"status": "completed", "id": obligation_id}


@router.patch("/{obligation_id}")
async def update_obligation(
    obligation_id: str,
    data: ObligationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update obligation"""
    values = {k: v for k, v in data.dict().items() if v is not None}
    if values:
        await db.execute(
            update(Obligation)
            .where(Obligation.id == obligation_id)
            .values(**values)
        )
        await db.commit()
    return {"status": "updated", "id": obligation_id}


@router.delete("/{obligation_id}")
async def delete_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete obligation"""
    await db.execute(delete(Obligation).where(Obligation.id == obligation_id))
    await db.commit()
    return {"status": "deleted", "id": obligation_id}