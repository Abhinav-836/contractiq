from typing import Optional, List

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import gen_uuid
from modules.alerts.models import Alert


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
        )
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def get_by_id(self, alert_id: str) -> Optional[Alert]:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def get_by_contract(self, contract_id: str) -> List[Alert]:
        result = await self.db.execute(
            select(Alert).where(Alert.contract_id == contract_id).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(
        self, unread_only: bool = False, type: Optional[str] = None,
        skip: int = 0, limit: int = 50,
    ) -> List[Alert]:
        q = select(Alert).order_by(Alert.created_at.desc())
        if unread_only:
            q = q.where(Alert.read.is_(False))
        if type:
            q = q.where(Alert.type == type)
        q = q.offset(skip).limit(limit)
        return list((await self.db.execute(q)).scalars().all())

    async def mark_as_read(self, alert_id: str):
        await self.db.execute(update(Alert).where(Alert.id == alert_id).values(read=True))
        await self.db.flush()

    async def mark_all_as_read(self):
        await self.db.execute(update(Alert).values(read=True))
        await self.db.flush()

    async def delete(self, alert_id: str):
        await self.db.execute(delete(Alert).where(Alert.id == alert_id))
        await self.db.flush()

    async def get_stats(self) -> dict:
        total = (await self.db.execute(select(func.count(Alert.id)))).scalar() or 0
        unread = (
            await self.db.execute(select(func.count(Alert.id)).where(Alert.read.is_(False)))
        ).scalar() or 0
        return {"total": total, "unread": unread}