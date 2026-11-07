"""built-in e-signature: envelopes, signers, audit events; contracts.signature_status

Revision ID: 0004_signatures
Revises: 0003_approvals
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_signatures"
down_revision: Union[str, None] = "0003_approvals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signature_envelopes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("contract_id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("requested_by", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("document_sha256", sa.String(), nullable=False),
        sa.Column("document_filename", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signature_envelopes_contract_id", "signature_envelopes", ["contract_id"])
    op.create_index("ix_signature_envelopes_workspace_id", "signature_envelopes", ["workspace_id"])
    op.create_index("ix_signature_envelopes_status", "signature_envelopes", ["status"])

    op.create_table(
        "signature_signers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("envelope_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("typed_signature", sa.String(), nullable=True),
        sa.Column("consent_text", sa.Text(), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["envelope_id"], ["signature_envelopes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_signature_signers_token_hash"),
    )
    op.create_index("ix_signature_signers_envelope_id", "signature_signers", ["envelope_id"])

    op.create_table(
        "signature_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("envelope_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["envelope_id"], ["signature_envelopes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signature_events_envelope_id", "signature_events", ["envelope_id"])

    with op.batch_alter_table("contracts") as batch:
        batch.add_column(sa.Column("signature_status", sa.String(), nullable=True))
        batch.create_index("ix_contracts_signature_status", ["signature_status"])


def downgrade() -> None:
    with op.batch_alter_table("contracts") as batch:
        batch.drop_index("ix_contracts_signature_status")
        batch.drop_column("signature_status")
    op.drop_index("ix_signature_events_envelope_id", table_name="signature_events")
    op.drop_table("signature_events")
    op.drop_index("ix_signature_signers_envelope_id", table_name="signature_signers")
    op.drop_table("signature_signers")
    for name in ("status", "workspace_id", "contract_id"):
        op.drop_index(f"ix_signature_envelopes_{name}", table_name="signature_envelopes")
    op.drop_table("signature_envelopes")
