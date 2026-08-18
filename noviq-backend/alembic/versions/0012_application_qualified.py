"""applications: add auto-computed qualified flag

Revision ID: 0012_application_qualified
Revises: 0011_nullable_owner_fk
Create Date: 2026-08-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_application_qualified"
down_revision: Union[str, None] = "0011_nullable_owner_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable, no backfill: existing rows (if any) get NULL, meaning "not
    # yet computed" — the same meaning it carries going forward for an
    # application whose match/analysis scores weren't both available.
    op.add_column("applications", sa.Column("qualified", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "qualified")
