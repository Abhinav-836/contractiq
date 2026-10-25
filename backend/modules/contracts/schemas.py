from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ContractListItem(BaseModel):
    """Lightweight row for list views (no extracted text, no server file path)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    risk_level: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContractOut(ContractListItem):
    extracted_text: Optional[str] = None


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