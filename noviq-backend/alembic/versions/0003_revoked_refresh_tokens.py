"""revoked refresh tokens

Revision ID: 0003_revoked_refresh_tokens
Revises: 0002_ats_ai_section_job_match
Create Date: 2026-08-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_revoked_refresh_tokens"
down_revision: Union[str, None] = "0002_ats_ai_section_job_match"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revoked_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("jti", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_revoked_refresh_tokens_jti", "revoked_refresh_tokens", ["jti"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_revoked_refresh_tokens_jti", "revoked_refresh_tokens")
    op.drop_table("revoked_refresh_tokens")
