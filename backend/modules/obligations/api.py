from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import require_auth
from .models import Obligation
from .schemas import ObligationOut, ObligationUpdate

router = APIRouter()


@router.get("", response_model=List[ObligationOut])
async def list_obligations(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
    contract_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    q = select(Obligation).order_by(Obligation.created_at.desc())
    if contract_id:
        q = q.where(Obligation.contract_id == contract_id)
    if status:
        q = q.where(Obligation.status == status)
    if priority:
        q = q.where(Obligation.priority == priority)
    q = q.offset(skip).limit(limit)
    return list((await db.execute(q)).scalars().all())


@router.get("/stats")
async def get_obligation_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    async def count(where=None) -> int:
        q = select(func.count(Obligation.id))
        if where is not None:
            q = q.where(where)
        return (await db.execute(q)).scalar() or 0

    return {
        "total": await count(),
        "overdue": await count(Obligation.status == "pending"),
        "pending": await count(Obligation.status == "pending"),
        "completed": await count(Obligation.status == "completed"),
    }


@router.get("/{obligation_id}", response_model=ObligationOut)
async def get_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    result = await db.execute(select(Obligation).where(Obligation.id == obligation_id))
    obligation = result.scalar_one_or_none()
    if not obligation:
        raise HTTPException(404, "Obligation not found")
    return obligation


@router.patch("/{obligation_id}/complete")
async def complete_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    await db.execute(
        update(Obligation).where(Obligation.id == obligation_id).values(status="completed")
    )
    await db.commit()
    return {"status": "completed", "id": obligation_id}


@router.patch("/{obligation_id}")
async def update_obligation(
    obligation_id: str,
    data: ObligationUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    values = {k: v for k, v in data.model_dump().items() if v is not None}
    if values:
        await db.execute(
            update(Obligation).where(Obligation.id == obligation_id).values(**values)
        )
        await db.commit()
    return {"status": "updated", "id": obligation_id}


@router.delete("/{obligation_id}")
async def delete_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    await db.execute(delete(Obligation).where(Obligation.id == obligation_id))
    await db.commit()
    return {"status": "deleted", "id": obligation_id}