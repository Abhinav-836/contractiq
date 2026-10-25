from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import require_auth
from modules.contracts.repository import owned_contract_ids
from .models import Obligation
from .schemas import ObligationOut, ObligationUpdate, ObligationStatsOut

router = APIRouter()

VALID_STATUSES = {"pending", "completed", "overdue", "upcoming"}
VALID_PRIORITIES = {"low", "medium", "high"}


def _mine(user_id: str):
    """Every query is restricted to obligations on the caller's own contracts."""
    return Obligation.contract_id.in_(owned_contract_ids(user_id))


async def _get_owned(db: AsyncSession, obligation_id: str, user_id: str) -> Obligation:
    result = await db.execute(
        select(Obligation).where(Obligation.id == obligation_id, _mine(user_id))
    )
    obligation = result.scalar_one_or_none()
    if not obligation:
        raise HTTPException(404, "Obligation not found")
    return obligation


@router.get("", response_model=List[ObligationOut])
async def list_obligations(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
    contract_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    q = select(Obligation).where(_mine(user_id)).order_by(Obligation.created_at.desc())
    if contract_id:
        q = q.where(Obligation.contract_id == contract_id)
    if status:
        q = q.where(Obligation.status == status)
    if priority:
        q = q.where(Obligation.priority == priority)
    q = q.offset(skip).limit(limit)
    return list((await db.execute(q)).scalars().all())


@router.get("/stats", response_model=ObligationStatsOut)
async def get_obligation_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    async def count(where=None) -> int:
        q = select(func.count(Obligation.id)).where(_mine(user_id))
        if where is not None:
            q = q.where(where)
        return (await db.execute(q)).scalar() or 0

    return {
        "total": await count(),
        # was `status == "pending"`, so "Overdue" always mirrored "Pending"
        "overdue": await count(Obligation.status == "overdue"),
        "pending": await count(Obligation.status == "pending"),
        "completed": await count(Obligation.status == "completed"),
    }


@router.get("/{obligation_id}", response_model=ObligationOut)
async def get_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    return await _get_owned(db, obligation_id, user_id)


@router.patch("/{obligation_id}/complete")
async def complete_obligation(
    obligation_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    await _get_owned(db, obligation_id, user_id)
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
    await _get_owned(db, obligation_id, user_id)
    values = {
        k: v for k, v in data.model_dump(exclude_unset=True).items()
        # these columns are NOT NULL — an explicit null would raise an IntegrityError
        if not (v is None and k in ("title", "status", "priority"))
    }
    if "status" in values and values["status"] not in VALID_STATUSES:
        raise HTTPException(422, f"status must be one of {sorted(VALID_STATUSES)}")
    if "priority" in values and values["priority"] not in VALID_PRIORITIES:
        raise HTTPException(422, f"priority must be one of {sorted(VALID_PRIORITIES)}")
    if values.get("title") is not None and not values["title"].strip():
        raise HTTPException(422, "title cannot be empty")
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
    await _get_owned(db, obligation_id, user_id)
    await db.execute(delete(Obligation).where(Obligation.id == obligation_id))
    await db.commit()
    return {"status": "deleted", "id": obligation_id}