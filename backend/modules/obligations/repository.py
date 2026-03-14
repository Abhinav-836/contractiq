# modules/obligations/repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from modules.obligations.models import Obligation
from db.base import gen_uuid
from typing import Optional, List
from datetime import datetime


class ObligationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, contract_id: str, title: str, description: str = None, 
                     due_date: Optional[str] = None, priority: str = "medium") -> Obligation:
        """Create a new obligation - FIXED: removed obligated_party"""
        obligation = Obligation(
            id=gen_uuid(),
            contract_id=contract_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status="pending"
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

    async def list_all(self, contract_id: Optional[str] = None, 
                       status: Optional[str] = None,
                       priority: Optional[str] = None,
                       skip: int = 0, limit: int = 50) -> List[Obligation]:
        query = select(Obligation).order_by(Obligation.created_at.desc())
        
        if contract_id:
            query = query.where(Obligation.contract_id == contract_id)
        if status:
            query = query.where(Obligation.status == status)
        if priority:
            query = query.where(Obligation.priority == priority)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(self, obligation_id: str, status: str):
        await self.db.execute(
            update(Obligation)
            .where(Obligation.id == obligation_id)
            .values(status=status)
        )
        await self.db.flush()

    async def delete(self, obligation_id: str):
        await self.db.execute(
            delete(Obligation).where(Obligation.id == obligation_id)
        )
        await self.db.flush()

    async def get_stats(self) -> dict:
        total = await self.db.execute(select(Obligation))
        total_count = len(total.scalars().all())
        
        # FIXED: Handle due_date comparison properly
        now = datetime.now().isoformat()
        overdue_query = await self.db.execute(
            select(Obligation).where(
                Obligation.status == "pending",
                Obligation.due_date < now
            )
        )
        overdue_count = len(overdue_query.scalars().all())
        
        pending_query = await self.db.execute(
            select(Obligation).where(Obligation.status == "pending")
        )
        pending_count = len(pending_query.scalars().all())
        
        completed_query = await self.db.execute(
            select(Obligation).where(Obligation.status == "completed")
        )
        completed_count = len(completed_query.scalars().all())
        
        return {
            "total": total_count,
            "overdue": overdue_count,
            "pending": pending_count,
            "completed": completed_count,
        }