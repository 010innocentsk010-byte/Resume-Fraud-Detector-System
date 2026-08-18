"""job postings and applications: public apply-link intake pipeline

Revision ID: 0009_job_postings_and_applications
Revises: 0008_document_evidence_source
Create Date: 2026-08-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_job_postings_apps"
down_revision: Union[str, None] = "0008_document_evidence_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create_type=False: created explicitly below via .create(checkfirst=True),
    # see 0001_initial's note on why (avoids create_table() double-CREATE-TYPE).
    job_posting_status = postgresql.ENUM("draft", "published", "closed", name="job_posting_status", create_type=False)
    application_status = postgresql.ENUM(
        "new", "reviewed", "shortlisted", "rejected", "hired", name="application_status", create_type=False
    )
    application_source = postgresql.ENUM("public_link", "manual", name="application_source", create_type=False)

    bind = op.get_bind()
    job_posting_status.create(bind, checkfirst=True)
    application_status.create(bind, checkfirst=True)
    application_source.create(bind, checkfirst=True)

    op.create_table(
        "job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("career_field", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("parsed_skills", postgresql.JSONB, server_default="[]"),
        sa.Column("status", job_posting_status, nullable=False, server_default="draft"),
        sa.Column("public_token", sa.String(64), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_job_postings_public_token", "job_postings", ["public_token"], unique=True)

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "job_posting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applicants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("job_match_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_matches.id"), nullable=True),
        sa.Column("status", application_status, nullable=False, server_default="new"),
        sa.Column("source", application_source, nullable=False),
        sa.UniqueConstraint("job_posting_id", "applicant_id", name="uq_application_posting_applicant"),
    )
    op.create_index("ix_applications_job_posting_id", "applications", ["job_posting_id"])
    op.create_index("ix_applications_applicant_id", "applications", ["applicant_id"])
    op.create_index("ix_applications_status", "applications", ["status"])


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("job_postings")

    bind = op.get_bind()
    postgresql.ENUM(name="application_source").drop(bind, checkfirst=True)
    postgresql.ENUM(name="application_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="job_posting_status").drop(bind, checkfirst=True)
