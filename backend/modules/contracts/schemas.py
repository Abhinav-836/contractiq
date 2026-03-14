from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ContractBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    status: str
    risk_level: Optional[str] = None


class ContractCreate(ContractBase):
    file_path: str
    user_id: Optional[str] = None


class ContractOut(ContractBase):
    id: str
    file_path: str
    extracted_text: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractStatsOut(BaseModel):
    total_contracts: int
    processing: int
    completed: int
    failed: int
    high_risk: int
    medium_risk: int
    low_risk: int


class ContractUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str


class ContractListResponse(BaseModel):
    contracts: List[ContractOut]
    total: int
    page: int
    limit: int


class ContractUpdateStatus(BaseModel):
    status: str
    risk_level: Optional[str] = None
    extracted_text: Optional[str] = None