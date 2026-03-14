from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from modules.alerts.models import Alert
from db.base import gen_uuid
from typing import Optional, List
from datetime import datetime


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, contract_id: str, type: str, title: str, message: str) -> Alert:
        alert = Alert(
            id=gen_uuid(),
            contract_id=contract_id,
            type=type,
            title=title,
            message=message,
            read=False,
            created_at=datetime.now()
        )
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def get_by_id(self, alert_id: str) -> Optional[Alert]:
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def get_by_contract(self, contract_id: str) -> List[Alert]:
        result = await self.db.execute(
            select(Alert)
            .where(Alert.contract_id == contract_id)
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self, unread_only: bool = False, 
                       type: Optional[str] = None,
                       skip: int = 0, limit: int = 50) -> List[Alert]:
        query = select(Alert).order_by(Alert.created_at.desc())
        
        if unread_only:
            query = query.where(Alert.read == False)
        if type:
            query = query.where(Alert.type == type)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_as_read(self, alert_id: str):
        await self.db.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(read=True)
        )
        await self.db.flush()

    async def mark_all_as_read(self):
        await self.db.execute(
            update(Alert).values(read=True)
        )
        await self.db.flush()

    async def delete(self, alert_id: str):
        await self.db.execute(
            delete(Alert).where(Alert.id == alert_id)
        )
        await self.db.flush()

    async def get_stats(self) -> dict:
        total = await self.db.execute(select(Alert))
        total_count = len(total.scalars().all())
        
        unread = await self.db.execute(
            select(Alert).where(Alert.read == False)
        )
        unread_count = len(unread.scalars().all())
        
        return {
            "total": total_count,
            "unread": unread_count,
        }