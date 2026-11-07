from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ApprovalCreate(BaseModel):
    reviewer_ids: List[str] = Field(min_length=1, max_length=10)
    note: Optional[str] = Field(None, max_length=2000)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewerOut(BaseModel):
    user_id: str
    name: str
    decision: Optional[str]
    comment: Optional[str]
    decided_at: Optional[datetime]


class ApprovalOut(BaseModel):
    id: str
    contract_id: str
    contract_filename: Optional[str]
    status: str
    note: Optional[str]
    requested_by: Optional[str]
    requested_by_name: str
    created_at: Optional[datetime]
    closed_at: Optional[datetime]
    closed_by_name: Optional[str]
    reviewers: List[ReviewerOut]
    approved_count: int
    awaiting_my_decision: bool


class ApprovalStatsOut(BaseModel):
    waiting_for_me: int
    pending: int
