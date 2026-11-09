from sqlalchemy import Column, DateTime, ForeignKey, String

from db.base import Base, gen_uuid


class AIRun(Base):
    """
    One row per AI contract review started (upload or "Review again").
    Counted for the daily limits in modules/usage/service.py, so one person
    or a burst of sign-ups can't run up the AI provider bill.
    """
    __tablename__ = "ai_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
