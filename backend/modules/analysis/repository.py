import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.analysis.models import Analysis
from db.base import gen_uuid
from typing import Optional


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, contract_id: str, data: dict, llm_provider: str = "mock") -> Analysis:
        analysis = Analysis(
            id=gen_uuid(),
            contract_id=contract_id,
            executive_summary=data.get("executive_summary"),
            summary=data.get("summary"),
            risk_score=data.get("risk_score"),
            risk_level=data.get("risk_level"),
            clauses=json.dumps(data.get("clauses", [])),
            recommendations=json.dumps(data.get("recommendations", [])),
            parties=json.dumps(data.get("parties", [])),
            key_dates=json.dumps(data.get("key_dates", [])),
            llm_provider=llm_provider,
        )
        self.db.add(analysis)
        await self.db.flush()
        return analysis

    async def get_by_contract(self, contract_id: str) -> Optional[Analysis]:
        result = await self.db.execute(
            select(Analysis).where(Analysis.contract_id == contract_id)
        )
        return result.scalar_one_or_none()

    def serialize(self, analysis: Analysis) -> dict:
        """Convert Analysis ORM to dict with parsed JSON fields."""
        d = {
            "id": analysis.id,
            "contract_id": analysis.contract_id,
            "executive_summary": analysis.executive_summary,
            "summary": analysis.summary,
            "risk_score": analysis.risk_score,
            "risk_level": analysis.risk_level,
            "llm_provider": analysis.llm_provider,
            "created_at": analysis.created_at,
        }
        for field in ("clauses", "recommendations", "parties", "key_dates"):
            raw = getattr(analysis, field)
            try:
                d[field] = json.loads(raw) if raw else []
            except Exception:
                d[field] = []
        return d
