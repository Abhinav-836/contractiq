from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ObligationBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None
    contract_id: str
    obligated_party: Optional[str] = None


class ObligationCreate(ObligationBase):
    pass


class ObligationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None


class ObligationOut(ObligationBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ObligationStatsOut(BaseModel):
    total: int
    overdue: int
    pending: int
    completed: int


class ObligationListResponse(BaseModel):
    obligations: List[ObligationOut]
    total: int
    page: int
    limit: int