from typing import Optional, List

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import gen_uuid
from modules.contracts.models import Contract, ContractFile
from core.constants import ContractStatus


def owned_contract_ids(user_id: str):
    """Subquery of contract ids belonging to a user — used to scope obligations/alerts/analyses."""
    return select(Contract.id).where(Contract.user_id == user_id)


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
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Contract]:
        q = (
            select(Contract)
            .where(Contract.user_id == user_id)
            .order_by(Contract.created_at.desc())
        )
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

    async def delete_with_children(self, contract_id: str):
        """
        Explicitly delete children. SQLite does not enforce ON DELETE CASCADE
        unless PRAGMA foreign_keys=ON, so obligations/alerts were left orphaned
        and kept showing up in the Obligations/Alerts pages.
        """
        from modules.analysis.models import Analysis
        from modules.obligations.models import Obligation
        from modules.alerts.models import Alert

        for model in (Analysis, Obligation, Alert, ContractFile):
            await self.db.execute(delete(model).where(model.contract_id == contract_id))
        await self.db.execute(delete(Contract).where(Contract.id == contract_id))
        await self.db.flush()

    async def stats(self, user_id: str) -> dict:
        async def count(where_clause=None) -> int:
            q = select(func.count(Contract.id)).where(Contract.user_id == user_id)
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