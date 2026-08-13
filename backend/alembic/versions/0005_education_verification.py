"""education verification: verified_schools + verification_logs

Revision ID: 0005_education_verification
Revises: 0004_career_fields
Create Date: 2026-08-10

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_education_verification"
down_revision: Union[str, None] = "0004_career_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fictional demo records only — not real students or alumni.
SEED_SCHOOLS = [
    {"full_name": "Kwesi Owusu", "school_name": "University of Ghana", "degree": "BSc Computer Science", "graduation_year": 2019},
    {"full_name": "Akosua Boateng", "school_name": "University of Ghana", "degree": "BA Economics", "graduation_year": 2021},
    {"full_name": "Yaw Mensah", "school_name": "University of Ghana", "degree": "BSc Business Administration", "graduation_year": 2018},
    {"full_name": "Abena Asante", "school_name": "Kwame Nkrumah University of Science and Technology", "degree": "BSc Electrical Engineering", "graduation_year": 2020},
    {"full_name": "Kofi Adjei", "school_name": "Kwame Nkrumah University of Science and Technology", "degree": "BSc Computer Engineering", "graduation_year": 2022},
    {"full_name": "Ama Darko", "school_name": "Kwame Nkrumah University of Science and Technology", "degree": "MSc Information Technology", "graduation_year": 2023},
    {"full_name": "Kwabena Appiah", "school_name": "Kwame Nkrumah University of Science and Technology", "degree": "BSc Civil Engineering", "graduation_year": 2017},
    {"full_name": "Efua Sarpong", "school_name": "University of Cape Coast", "degree": "BEd Mathematics", "graduation_year": 2019},
    {"full_name": "Yaa Amponsah", "school_name": "University of Cape Coast", "degree": "BSc Nursing", "graduation_year": 2021},
    {"full_name": "Nana Kwame", "school_name": "University of Cape Coast", "degree": "BA English", "graduation_year": 2020},
]


def upgrade() -> None:
    verification_status = postgresql.ENUM(
        "verified", "not_found", "pending", "error", name="verification_status", create_type=False
    )
    verification_source = postgresql.ENUM("local_db", "ghana_api", name="verification_source", create_type=False)

    bind = op.get_bind()
    verification_status.create(bind, checkfirst=True)
    verification_source.create(bind, checkfirst=True)

    op.create_table(
        "verified_schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("school_name", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(255), nullable=False),
        sa.Column("graduation_year", sa.Integer, nullable=False),
    )
    op.create_index("ix_verified_schools_full_name", "verified_schools", ["full_name"])
    op.create_index("ix_verified_schools_school_name", "verified_schools", ["school_name"])

    op.create_table(
        "verification_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("applicant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applicants.id"), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("school_name", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(255), nullable=False),
        sa.Column("graduation_year", sa.Integer, nullable=False),
        sa.Column("candidate_consent", sa.Boolean, nullable=False),
        sa.Column("status", verification_status, nullable=False),
        sa.Column("verified_by", verification_source, nullable=True),
    )

    verified_schools_table = sa.table(
        "verified_schools",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("full_name", sa.String),
        sa.column("school_name", sa.String),
        sa.column("degree", sa.String),
        sa.column("graduation_year", sa.Integer),
    )
    op.bulk_insert(
        verified_schools_table,
        [{"id": uuid.uuid4(), **row} for row in SEED_SCHOOLS],
    )


def downgrade() -> None:
    op.drop_table("verification_logs")
    op.drop_table("verified_schools")

    bind = op.get_bind()
    postgresql.ENUM(name="verification_source").drop(bind, checkfirst=True)
    postgresql.ENUM(name="verification_status").drop(bind, checkfirst=True)
