from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AlertBase(BaseModel):
    contract_id: Optional[str] = None
    type: str
    title: str
    message: str
    read: bool = False


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    read: Optional[bool] = None
    title: Optional[str] = None
    message: Optional[str] = None


class AlertOut(AlertBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AlertStatsOut(BaseModel):
    total: int
    unread: int


class AlertListResponse(BaseModel):
    alerts: List[AlertOut]
    total: int
    unread: int
    page: int
    limit: int