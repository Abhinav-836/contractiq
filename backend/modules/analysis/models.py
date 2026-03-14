from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, func
from db.base import Base, gen_uuid


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, unique=True, index=True)
    executive_summary = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    clauses = Column(Text, nullable=True)           # JSON array
    recommendations = Column(Text, nullable=True)   # JSON array
    parties = Column(Text, nullable=True)           # JSON array
    key_dates = Column(Text, nullable=True)         # JSON array
    llm_provider = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
