"""approval requests and reviewers; contracts.approval_status

Revision ID: 0003_approvals
Revises: 0002_workspaces
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_approvals"
down_revision: Union[str, None] = "0002_workspaces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("contract_id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("requested_by", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["closed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_requests_contract_id", "approval_requests", ["contract_id"])
    op.create_index("ix_approval_requests_workspace_id", "approval_requests", ["workspace_id"])
    op.create_index("ix_approval_requests_requested_by", "approval_requests", ["requested_by"])
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])

    op.create_table(
        "approval_reviewers",
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["approval_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("request_id", "user_id"),
    )
    op.create_index("ix_approval_reviewers_user_id", "approval_reviewers", ["user_id"])

    with op.batch_alter_table("contracts") as batch:
        batch.add_column(sa.Column("approval_status", sa.String(), nullable=True))
        batch.create_index("ix_contracts_approval_status", ["approval_status"])


def downgrade() -> None:
    with op.batch_alter_table("contracts") as batch:
        batch.drop_index("ix_contracts_approval_status")
        batch.drop_column("approval_status")
    op.drop_index("ix_approval_reviewers_user_id", table_name="approval_reviewers")
    op.drop_table("approval_reviewers")
    for name in ("status", "requested_by", "workspace_id", "contract_id"):
        op.drop_index(f"ix_approval_requests_{name}", table_name="approval_requests")
    op.drop_table("approval_requests")
