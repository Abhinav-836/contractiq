from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, LargeBinary, func
from db.base import Base, gen_uuid


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=gen_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    # Legacy: on-disk path for contracts uploaded before files moved into the DB.
    # New uploads store "db" here and keep the bytes in contract_files.
    file_path = Column(String, nullable=False)
    status = Column(String, default="processing", nullable=False, index=True)
    risk_level = Column(String, nullable=True, index=True)
    extracted_text = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ContractFile(Base):
    """
    Original uploaded file bytes, kept in Postgres.

    Render's disk is wiped on every deploy/restart, so files written to
    uploads/ vanished and "Retry analysis" on older contracts failed.
    A separate table keeps the large blob out of every SELECT on contracts.
    """
    __tablename__ = "contract_files"

    contract_id = Column(
        String,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())