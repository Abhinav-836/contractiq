from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# Fields default to "" so analyses saved before normalization (or with a sparse
# LLM response) still serialize instead of failing validation with a 500.
class ClauseOut(BaseModel):
    clause_type: str = "Clause"
    risk_level: str = "medium"
    clause_text: str = ""
    explanation: str = ""
    recommendation: Optional[str] = None


class KeyDateOut(BaseModel):
    label: str = "Date"
    date: str = ""


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contract_id: str
    executive_summary: Optional[str] = None
    summary: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    llm_provider: Optional[str] = None
    clauses: List[ClauseOut] = []
    recommendations: List[str] = []
    parties: List[str] = []
    key_dates: List[KeyDateOut] = []
    created_at: Optional[datetime] = None