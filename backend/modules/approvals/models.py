from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func

from db.base import Base, gen_uuid


class ApprovalRequest(Base):
    """
    Someone asks named reviewers to sign off a contract.
    Approved when every reviewer approves; rejected as soon as one rejects.
    """
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(
        String, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id = Column(
        String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    note = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending", index=True)  # pending | approved | rejected | cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class ApprovalReviewer(Base):
    __tablename__ = "approval_reviewers"

    request_id = Column(
        String, ForeignKey("approval_requests.id", ondelete="CASCADE"), primary_key=True
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    decision = Column(String, nullable=True)  # None (waiting) | approved | rejected
    comment = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
