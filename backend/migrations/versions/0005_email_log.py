"""email log for notification emails (signing links, approvals)

Revision ID: 0005_email_log
Revises: 0004_signatures
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_email_log"
down_revision: Union[str, None] = "0004_signatures"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("to_email", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("provider_message_id", sa.String(), nullable=True),
        sa.Column("ref_type", sa.String(), nullable=True),
        sa.Column("ref_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_log_workspace_id", "email_log", ["workspace_id"])
    op.create_index("ix_email_log_ref_id", "email_log", ["ref_id"])
    op.create_index("ix_email_log_created_at", "email_log", ["created_at"])


def downgrade() -> None:
    for name in ("created_at", "ref_id", "workspace_id"):
        op.drop_index(f"ix_email_log_{name}", table_name="email_log")
    op.drop_table("email_log")
