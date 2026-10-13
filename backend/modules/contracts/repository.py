from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import gen_uuid
from modules.contracts.models import Contract
from core.constants import ContractStatus

from typing import Optional, List


class ContractRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        user_id: Optional[str] = None,
    ) -> Contract:
        contract = Contract(
            id=gen_uuid(),
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            user_id=user_id,
            status=ContractStatus.PROCESSING.value,
        )
        self.db.add(contract)
        await self.db.flush()
        return contract

    async def get_by_id(self, contract_id: str) -> Optional[Contract]:
        result = await self.db.execute(select(Contract).where(Contract.id == contract_id))
        return result.scalar_one_or_none()

    async def list_all(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Contract]:
        q = select(Contract).order_by(Contract.created_at.desc())
        if user_id:
            q = q.where(Contract.user_id == user_id)
        if status:
            q = q.where(Contract.status == status)
        q = q.offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def update_file_path(self, contract_id: str, file_path: str):
        await self.db.execute(
            update(Contract)
            .where(Contract.id == contract_id)
            .values(file_path=file_path, updated_at=func.now())
        )
        await self.db.flush()

    async def update_status(
        self,
        contract_id: str,
        status: str,
        risk_level: Optional[str] = None,
        extracted_text: Optional[str] = None,
    ):
        values = {"status": status, "updated_at": func.now()}
        if risk_level:
            values["risk_level"] = risk_level
        if extracted_text is not None:
            values["extracted_text"] = extracted_text
        await self.db.execute(
            update(Contract).where(Contract.id == contract_id).values(**values)
        )
        await self.db.flush()

    async def stats(self) -> dict:
        async def count(where_clause=None) -> int:
            q = select(func.count(Contract.id))
            if where_clause is not None:
                q = q.where(where_clause)
            return (await self.db.execute(q)).scalar() or 0

        return {
            "total_contracts": await count(),
            "processing": await count(Contract.status == "processing"),
            "completed": await count(Contract.status == "completed"),
            "failed": await count(Contract.status == "failed"),
            "high_risk": await count(Contract.risk_level == "high"),
            "medium_risk": await count(Contract.risk_level == "medium"),
            "low_risk": await count(Contract.risk_level == "low"),
        }