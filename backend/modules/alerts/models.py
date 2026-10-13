from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from db.base import Base, gen_uuid


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(
        String,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())