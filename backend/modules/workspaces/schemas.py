from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, EmailStr

AssignableRole = Literal["admin", "member", "viewer"]


class _Named(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def strip(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Name can't be empty")
        return v


class WorkspaceCreate(_Named):
    pass


class WorkspaceRename(_Named):
    pass


class WorkspaceOut(BaseModel):
    id: str
    name: str
    is_personal: bool
    role: str
    member_count: int
    contract_count: int
    created_at: Optional[datetime] = None


class MemberOut(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    joined_at: Optional[datetime] = None
    is_you: bool


class RoleUpdate(BaseModel):
    role: AssignableRole


class InviteCreate(BaseModel):
    role: AssignableRole = "member"
    expires_in_days: int = Field(7, ge=1, le=30)
    max_uses: Optional[int] = Field(None, ge=1, le=100)
    # Optional: email the invite link to this address (when email is set up).
    email: Optional[EmailStr] = None


class InviteOut(BaseModel):
    id: str
    role: str
    expires_at: datetime
    max_uses: Optional[int]
    use_count: int
    created_at: Optional[datetime] = None
    created_by_name: Optional[str] = None


class InviteCreated(InviteOut):
    token: str  # shown once
    emailed_to: Optional[str] = None  # set when an invite email was queued


class InvitePreview(BaseModel):
    workspace_name: str
    role: str
    invited_by: Optional[str]
    expires_at: datetime


class InviteAccepted(BaseModel):
    workspace_id: str
    role: str
    already_member: bool
