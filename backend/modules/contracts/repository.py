from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from modules.contracts.models import Contract
from db.base import gen_uuid
from typing import Optional, List
from core.constants import ContractStatus


class ContractRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, filename: str, file_type: str, file_size: int,
                     file_path: str, user_id: Optional[str] = None) -> Contract:
        contract = Contract(
            id=gen_uuid(),
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            user_id=user_id,
            status=ContractStatus.PROCESSING,
        )
        self.db.add(contract)
        await self.db.flush()
        return contract

    async def get_by_id(self, contract_id: str) -> Optional[Contract]:
        result = await self.db.execute(select(Contract).where(Contract.id == contract_id))
        return result.scalar_one_or_none()

    async def list_all(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 50, status: Optional[str] = None) -> List[Contract]:
        q = select(Contract).order_by(Contract.created_at.desc())
        
        if user_id:
            q = q.where(Contract.user_id == user_id)
        if status:
            q = q.where(Contract.status == status)
            
        q = q.offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def update_status(self, contract_id: str, status: str,
                            risk_level: Optional[str] = None,
                            extracted_text: Optional[str] = None):
        values = {"status": status}
        if risk_level:
            values["risk_level"] = risk_level
        if extracted_text is not None:
            values["extracted_text"] = extracted_text
        await self.db.execute(update(Contract).where(Contract.id == contract_id).values(**values))
        await self.db.flush()

    async def stats(self) -> dict:
        total = (await self.db.execute(select(func.count(Contract.id)))).scalar() or 0
        processing = (await self.db.execute(select(func.count(Contract.id)).where(Contract.status == "processing"))).scalar() or 0
        completed = (await self.db.execute(select(func.count(Contract.id)).where(Contract.status == "completed"))).scalar() or 0
        failed = (await self.db.execute(select(func.count(Contract.id)).where(Contract.status == "failed"))).scalar() or 0
        high = (await self.db.execute(select(func.count(Contract.id)).where(Contract.risk_level == "high"))).scalar() or 0
        medium = (await self.db.execute(select(func.count(Contract.id)).where(Contract.risk_level == "medium"))).scalar() or 0
        low = (await self.db.execute(select(func.count(Contract.id)).where(Contract.risk_level == "low"))).scalar() or 0
        
        return {
            "total_contracts": total,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "high_risk": high,
            "medium_risk": medium,
            "low_risk": low,
        }