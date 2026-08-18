"""applicants/resumes: allow no recruiter owner (public self-service intake)

Revision ID: 0011_nullable_applicant_resume_owner
Revises: 0010_job_match_posting_link
Create Date: 2026-08-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0011_nullable_owner_fk"
down_revision: Union[str, None] = "0010_job_match_posting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Pure relaxation — every existing row already has a value, this only
    # allows future rows (public job-posting applications) to omit one.
    op.alter_column("applicants", "created_by_id", nullable=True)
    op.alter_column("resumes", "uploaded_by_id", nullable=True)


def downgrade() -> None:
    op.alter_column("resumes", "uploaded_by_id", nullable=False)
    op.alter_column("applicants", "created_by_id", nullable=False)
