from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from db.base import Base, gen_uuid


class EmailLog(Base):
    """
    One row per email ContractIQ tried to send. Used for the daily caps,
    for showing "Emailed" / "Email failed" in the UI, and for debugging.
    """
    __tablename__ = "email_log"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    # signature_request | signature_link | signature_completed | signature_declined
    # | approval_requested | approval_decided
    kind = Column(String, nullable=False)
    to_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, nullable=False)  # sent | failed | skipped
    error = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    provider_message_id = Column(String, nullable=True)
    # What the email was about, e.g. ("signature_signer", <signer id>)
    ref_type = Column(String, nullable=True)
    ref_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
