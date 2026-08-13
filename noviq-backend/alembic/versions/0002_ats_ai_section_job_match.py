"""ats score, per-section ai detector, job match

Revision ID: 0002_ats_ai_section_job_match
Revises: 0001_initial
Create Date: 2026-08-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_ats_ai_section_job_match"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analysis", sa.Column("ats_score", sa.Float, server_default="0", nullable=False))
    op.add_column("analysis", sa.Column("ats_issues", postgresql.JSONB, server_default="[]", nullable=False))
    op.add_column("analysis", sa.Column("ai_section_scores", postgresql.JSONB, server_default="[]", nullable=False))
    op.create_index("ix_analysis_ats_score", "analysis", ["ats_score"])

    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("parsed_skills", postgresql.JSONB, server_default="[]"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_job_descriptions_created_by_id", "job_descriptions", ["created_by_id"])

    op.create_table(
        "job_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_description_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("match_score", sa.Float, server_default="0"),
        sa.Column("matched_skills", postgresql.JSONB, server_default="[]"),
        sa.Column("missing_skills", postgresql.JSONB, server_default="[]"),
        sa.Column("semantic_similarity", sa.Float, server_default="0"),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
    )
    op.create_index("ix_job_matches_resume_id", "job_matches", ["resume_id"])
    op.create_index("ix_job_matches_match_score", "job_matches", ["match_score"])


def downgrade() -> None:
    op.drop_table("job_matches")
    op.drop_table("job_descriptions")

    op.drop_index("ix_analysis_ats_score", "analysis")
    op.drop_column("analysis", "ai_section_scores")
    op.drop_column("analysis", "ats_issues")
    op.drop_column("analysis", "ats_score")
