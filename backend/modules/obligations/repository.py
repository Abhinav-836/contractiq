from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import gen_uuid
from modules.obligations.models import Obligation


class ObligationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        contract_id: str,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium",
    ) -> Obligation:
        obligation = Obligation(
            id=gen_uuid(),
            contract_id=contract_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status="pending",
        )
        self.db.add(obligation)
        await self.db.flush()
        return obligation

    async def get_by_id(self, obligation_id: str) -> Optional[Obligation]:
        result = await self.db.execute(
            select(Obligation).where(Obligation.id == obligation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_contract(self, contract_id: str) -> List[Obligation]:
        result = await self.db.execute(
            select(Obligation)
            .where(Obligation.contract_id == contract_id)
            .order_by(Obligation.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        contract_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Obligation]:
        q = select(Obligation).order_by(Obligation.created_at.desc())
        if contract_id:
            q = q.where(Obligation.contract_id == contract_id)
        if status:
            q = q.where(Obligation.status == status)
        if priority:
            q = q.where(Obligation.priority == priority)
        q = q.offset(skip).limit(limit)
        return list((await self.db.execute(q)).scalars().all())

    async def update_status(self, obligation_id: str, status: str):
        await self.db.execute(
            update(Obligation).where(Obligation.id == obligation_id).values(status=status)
        )
        await self.db.flush()

    async def delete(self, obligation_id: str):
        await self.db.execute(delete(Obligation).where(Obligation.id == obligation_id))
        await self.db.flush()

    async def get_stats(self) -> dict:
        total = (await self.db.execute(select(func.count(Obligation.id)))).scalar() or 0
        pending = (
            await self.db.execute(
                select(func.count(Obligation.id)).where(Obligation.status == "pending")
            )
        ).scalar() or 0
        completed = (
            await self.db.execute(
                select(func.count(Obligation.id)).where(Obligation.status == "completed")
            )
        ).scalar() or 0
        return {"total": total, "overdue": pending, "pending": pending, "completed": completed}