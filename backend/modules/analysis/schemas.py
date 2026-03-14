from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ClauseOut(BaseModel):
    clause_type: str
    risk_level: str
    clause_text: str
    explanation: str
    recommendation: Optional[str] = None


class KeyDateOut(BaseModel):
    label: str
    date: str


class AnalysisBase(BaseModel):
    contract_id: str
    executive_summary: Optional[str] = None
    summary: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    llm_provider: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    clauses: Optional[List[dict]] = None
    recommendations: Optional[List[str]] = None
    parties: Optional[List[str]] = None
    key_dates: Optional[List[dict]] = None


class AnalysisOut(AnalysisBase):
    id: str
    clauses: List[ClauseOut] = []
    recommendations: List[str] = []
    parties: List[str] = []
    key_dates: List[KeyDateOut] = []
    created_at: datetime

    class Config:
        from_attributes = True