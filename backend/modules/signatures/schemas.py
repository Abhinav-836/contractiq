from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class SignerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class EnvelopeCreate(BaseModel):
    signers: List[SignerIn] = Field(min_length=1, max_length=10)
    message: Optional[str] = Field(None, max_length=2000)
    # Email each signer their link (only when email is set up on the server).
    send_email: bool = True


class SignBody(BaseModel):
    typed_name: str = Field(min_length=1, max_length=120)
    consent: bool


class DeclineBody(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class SignerOut(BaseModel):
    id: str
    name: str
    email: str
    status: str
    typed_signature: Optional[str]
    consent_text: Optional[str]
    decline_reason: Optional[str]
    viewed_at: Optional[datetime]
    acted_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]
    email_status: Optional[str] = None  # sent | failed | skipped | None (never emailed)
    email_error: Optional[str] = None


class EventOut(BaseModel):
    type: str
    actor: Optional[str]
    detail: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class EnvelopeOut(BaseModel):
    id: str
    contract_id: str
    status: str
    message: Optional[str]
    document_filename: str
    document_sha256: str
    requested_by: Optional[str]
    requested_by_name: str
    created_at: Optional[datetime]
    closed_at: Optional[datetime]
    signers: List[SignerOut]
    signed_count: int
    can_manage: bool
    events: Optional[List[EventOut]] = None
    # signer_id -> raw link token. Only present in the response that created it.
    links: Optional[Dict[str, str]] = None
    # True when the links in this response are also being emailed.
    emailed: Optional[bool] = None


class PublicSigner(BaseModel):
    name: str
    email: str
    status: str
    typed_signature: Optional[str]
    acted_at: Optional[datetime]
    decline_reason: Optional[str]


class PublicSignerSummary(BaseModel):
    name: str
    status: str
    is_you: bool


class PublicSigningOut(BaseModel):
    envelope_status: str
    document_filename: str
    document_sha256: str
    message: Optional[str]
    requested_by_name: Optional[str]
    sent_at: Optional[datetime]
    consent_text: str
    signer: PublicSigner
    signers: List[PublicSignerSummary]
