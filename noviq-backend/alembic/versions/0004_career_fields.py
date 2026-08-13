"""career fields on applicants and job descriptions

Revision ID: 0004_career_fields
Revises: 0003_revoked_refresh_tokens
Create Date: 2026-08-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_career_fields"
down_revision: Union[str, None] = "0003_revoked_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("applicants", sa.Column("field_of_study", sa.String(255), nullable=True))
    op.add_column("job_descriptions", sa.Column("career_field", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("job_descriptions", "career_field")
    op.drop_column("applicants", "field_of_study")
