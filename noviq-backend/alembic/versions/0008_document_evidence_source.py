"""education verification: add document_evidence verification source

Revision ID: 0008_document_evidence_source
Revises: 0007_edu_verification_v3
Create Date: 2026-08-12

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008_document_evidence_source"
down_revision: Union[str, None] = "0007_edu_verification_v3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the transaction Alembic
    # normally wraps migrations in — needs its own autocommit block.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE verification_source ADD VALUE IF NOT EXISTS 'document_evidence'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; downgrading would require
    # recreating the type. Left as a no-op — safe, since pre-migration code
    # never wrote this value.
    pass
