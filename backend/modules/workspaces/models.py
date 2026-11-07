from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from db.base import Base, gen_uuid


class Workspace(Base):
    """
    A team. Contracts belong to a workspace; people get access through
    membership. Every user has one personal workspace (is_personal=True),
    created at sign-up, which is where their contracts go by default.
    """
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    is_personal = Column(Boolean, nullable=False, default=False, server_default="false")
    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id = Column(
        String, ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True
    )
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role = Column(String, nullable=False)  # owner | admin | member | viewer
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkspaceInvite(Base):
    """
    Shareable invite link. Only a SHA-256 hash of the token is stored; the raw
    token is shown once, when the link is created.
    """
    __tablename__ = "workspace_invites"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(
        String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)  # admin | member | viewer
    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    max_uses = Column(Integer, nullable=True)  # None = unlimited until expiry
    use_count = Column(Integer, nullable=False, default=0, server_default="0")
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
