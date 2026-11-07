"""workspaces, members, invites; contracts.workspace_id

Every existing user gets a personal workspace (as owner) and their existing
contracts move into it, so nothing changes for them on the day this ships.

Revision ID: 0002_workspaces
Revises: 0001_baseline
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_workspaces"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONTRACTS_WORKSPACE_FK = "fk_contracts_workspace_id_workspaces"


def personal_workspace_name(user_name: str) -> str:
    name = (user_name or "").strip() or "My"
    return f"{name}'s workspace"


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_personal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workspace_members",
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("workspace_id", "user_id"),
    )
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])
    op.create_table(
        "workspace_invites",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_workspace_invites_token_hash"),
    )
    op.create_index("ix_workspace_invites_workspace_id", "workspace_invites", ["workspace_id"])

    # batch mode: plain ALTER on Postgres, table rebuild on SQLite
    with op.batch_alter_table("contracts") as batch:
        batch.add_column(sa.Column("workspace_id", sa.String(), nullable=True))
        batch.create_index("ix_contracts_workspace_id", ["workspace_id"])
        batch.create_foreign_key(CONTRACTS_WORKSPACE_FK, "workspaces", ["workspace_id"], ["id"])

    # ── Data: a personal workspace per existing user, and move their contracts in ──
    bind = op.get_bind()
    users = sa.table("users", sa.column("id", sa.String), sa.column("name", sa.String))
    workspaces = sa.table(
        "workspaces",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("is_personal", sa.Boolean),
        sa.column("created_by", sa.String),
    )
    members = sa.table(
        "workspace_members",
        sa.column("workspace_id", sa.String),
        sa.column("user_id", sa.String),
        sa.column("role", sa.String),
    )
    contracts = sa.table("contracts", sa.column("user_id", sa.String), sa.column("workspace_id", sa.String))

    for user_id, user_name in bind.execute(sa.select(users.c.id, users.c.name)).all():
        workspace_id = str(uuid.uuid4())
        bind.execute(
            workspaces.insert().values(
                id=workspace_id,
                name=personal_workspace_name(user_name),
                is_personal=True,
                created_by=user_id,
            )
        )
        bind.execute(members.insert().values(workspace_id=workspace_id, user_id=user_id, role="owner"))
        bind.execute(
            contracts.update().where(contracts.c.user_id == user_id).values(workspace_id=workspace_id)
        )
    # Contracts with no user_id (none should exist) stay with workspace_id NULL:
    # they were already invisible to everyone and remain so.


def downgrade() -> None:
    with op.batch_alter_table("contracts") as batch:
        batch.drop_constraint(CONTRACTS_WORKSPACE_FK, type_="foreignkey")
        batch.drop_index("ix_contracts_workspace_id")
        batch.drop_column("workspace_id")
    op.drop_index("ix_workspace_invites_workspace_id", table_name="workspace_invites")
    op.drop_table("workspace_invites")
    op.drop_index("ix_workspace_members_user_id", table_name="workspace_members")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
