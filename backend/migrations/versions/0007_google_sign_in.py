"""google sign-in

Revision ID: 0007_google_sign_in
Revises: 0006_auth_tokens

Adds users.google_sub: Google's permanent ID for a person, set the first
time they use "Sign in with Google". Accounts made with Google and no
password store "!google" as their password hash, which never matches.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_google_sign_in"
down_revision: Union[str, None] = "0006_auth_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("google_sub", sa.String(), nullable=True))
        batch.create_index("ix_users_google_sub", ["google_sub"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_google_sub")
        batch.drop_column("google_sub")
