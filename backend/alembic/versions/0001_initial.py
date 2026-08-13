"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create_type=False: these are created explicitly below via .create(checkfirst=True).
    # Leaving the default (True) makes create_table() below also try to CREATE TYPE,
    # which fails with DuplicateObject since it was just created.
    user_role = postgresql.ENUM("admin", "recruiter", name="user_role", create_type=False)
    resume_file_type = postgresql.ENUM("pdf", "docx", name="resume_file_type", create_type=False)
    resume_status = postgresql.ENUM(
        "uploaded", "parsing", "parsed", "analyzing", "analyzed", "failed", name="resume_status", create_type=False
    )
    risk_level = postgresql.ENUM("low", "medium", "high", name="risk_level", create_type=False)

    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    resume_file_type.create(bind, checkfirst=True)
    resume_status.create(bind, checkfirst=True)
    risk_level.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="recruiter"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("organization", sa.String(255), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "applicants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_applicants_email", "applicants", ["email"])

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("applicant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applicants.id"), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("file_type", resume_file_type, nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", resume_status, nullable=False, server_default="uploaded"),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("parsed_data", postgresql.JSONB, nullable=True),
        sa.Column("text_fingerprint", sa.String(64), nullable=True),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_resumes_text_fingerprint", "resumes", ["text_fingerprint"])

    op.create_table(
        "analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("experience_score", sa.Float, server_default="0"),
        sa.Column("education_score", sa.Float, server_default="0"),
        sa.Column("skill_score", sa.Float, server_default="0"),
        sa.Column("formatting_score", sa.Float, server_default="0"),
        sa.Column("timeline_score", sa.Float, server_default="0"),
        sa.Column("ai_score", sa.Float, server_default="0"),
        sa.Column("keyword_stuffing_score", sa.Float, server_default="0"),
        sa.Column("duplicate_score", sa.Float, server_default="0"),
        sa.Column("fraud_score", sa.Float, server_default="0"),
        sa.Column("risk_level", risk_level, nullable=False, server_default="low"),
        sa.Column("flags", postgresql.JSONB, server_default="[]"),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
    )
    op.create_index("ix_analysis_fraud_score", "analysis", ["fraud_score"])

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis.id"), nullable=False),
        sa.Column("recommendation", sa.Text, nullable=False),
        sa.Column("pdf_path", sa.String(1000), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("analysis")
    op.drop_table("resumes")
    op.drop_table("applicants")
    op.drop_table("users")

    bind = op.get_bind()
    postgresql.ENUM(name="risk_level").drop(bind, checkfirst=True)
    postgresql.ENUM(name="resume_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="resume_file_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="user_role").drop(bind, checkfirst=True)
