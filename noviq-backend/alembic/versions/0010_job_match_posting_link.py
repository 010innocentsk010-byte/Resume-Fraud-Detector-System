"""job_matches: allow scoring against a JobPosting, not just a JobDescription

Revision ID: 0010_job_match_posting_link
Revises: 0009_job_postings_and_applications
Create Date: 2026-08-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_job_match_posting"
down_revision: Union[str, None] = "0009_job_postings_apps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("job_matches", "job_description_id", nullable=True)
    op.add_column(
        "job_matches",
        sa.Column(
            "job_posting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_job_matches_job_posting_id", "job_matches", ["job_posting_id"])

    # Safe to add unconditionally in the same transaction: every existing row
    # already has job_description_id set and job_posting_id NULL (the column
    # was just added), so the constraint holds trivially for 100% of
    # pre-existing data the moment it's created.
    op.create_check_constraint(
        "ck_job_match_exactly_one_parent",
        "job_matches",
        "(job_description_id IS NOT NULL) != (job_posting_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_job_match_exactly_one_parent", "job_matches", type_="check")
    op.drop_index("ix_job_matches_job_posting_id", "job_matches")
    op.drop_column("job_matches", "job_posting_id")
    op.alter_column("job_matches", "job_description_id", nullable=False)
