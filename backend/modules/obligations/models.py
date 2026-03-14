from sqlalchemy import Column, String, DateTime, ForeignKey, func
from db.base import Base, gen_uuid


class Obligation(Base):
    __tablename__ = "obligations"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    due_date = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
