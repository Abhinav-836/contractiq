from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func

from db.base import Base, gen_uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    # Set when the person clicks the link emailed to this address; cleared when the email changes.
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class AuthToken(Base):
    """
    One-time links emailed to a user: password reset and email verification.
    Only the SHA-256 of the token is stored; the raw token exists only in the email.
    """
    __tablename__ = "auth_tokens"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose = Column(String, nullable=False)  # reset_password | verify_email
    token_hash = Column(String, nullable=False, unique=True)
    # The address the link was sent to. A verify link only counts for the address it went to.
    email = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
