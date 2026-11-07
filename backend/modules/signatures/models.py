from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from db.base import Base, gen_uuid


class SignatureEnvelope(Base):
    """
    A request for one or more people to sign a contract's file.
    Completed when every signer signs; declined as soon as one declines.
    """
    __tablename__ = "signature_envelopes"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending", index=True)  # pending | completed | declined | cancelled
    # SHA-256 of the exact file sent for signing, so the certificate proves what was signed.
    document_sha256 = Column(String, nullable=False)
    document_filename = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)


class SignatureSigner(Base):
    __tablename__ = "signature_signers"

    id = Column(String, primary_key=True, default=gen_uuid)
    envelope_id = Column(
        String, ForeignKey("signature_envelopes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    # SHA-256 of the signing-link token; the raw token is shown once.
    token_hash = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default="pending")  # pending | signed | declined
    typed_signature = Column(String, nullable=True)
    consent_text = Column(Text, nullable=True)
    decline_reason = Column(Text, nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)


class SignatureEvent(Base):
    """Append-only audit trail for an envelope."""
    __tablename__ = "signature_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    envelope_id = Column(
        String, ForeignKey("signature_envelopes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # created | link_reissued | emailed | viewed | signed | declined | completed | cancelled
    type = Column(String, nullable=False)
    actor = Column(String, nullable=True)  # a person's name, as shown on the certificate
    detail = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
