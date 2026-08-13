"""education verification: response_data audit column + more seed schools

Revision ID: 0006_edu_verification_v2
Revises: 0005_education_verification
Create Date: 2026-08-10

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_edu_verification_v2"
down_revision: Union[str, None] = "0005_education_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fictional demo records only — not real students or alumni.
SEED_SCHOOLS = [
    {"full_name": "Adjoa Frimpong", "school_name": "University of Education, Winneba", "degree": "BEd Science", "graduation_year": 2020},
    {"full_name": "Kojo Antwi", "school_name": "University of Education, Winneba", "degree": "BA Social Studies", "graduation_year": 2018},
    {"full_name": "Abigail Nkrumah", "school_name": "University of Education, Winneba", "degree": "BEd Early Childhood", "graduation_year": 2022},
    {"full_name": "Iddrisu Mohammed", "school_name": "University for Development Studies", "degree": "BSc Agriculture", "graduation_year": 2019},
    {"full_name": "Fuseina Alhassan", "school_name": "University for Development Studies", "degree": "BSc Community Nutrition", "graduation_year": 2021},
    {"full_name": "Salifu Yakubu", "school_name": "University for Development Studies", "degree": "BSc Renewable Energy", "graduation_year": 2023},
    {"full_name": "Nana Ama Baffour", "school_name": "Ashesi University", "degree": "BSc Computer Science", "graduation_year": 2021},
    {"full_name": "Kwabena Dua", "school_name": "Ashesi University", "degree": "BSc Business Administration", "graduation_year": 2020},
    {"full_name": "Selorm Agbeko", "school_name": "Ashesi University", "degree": "BSc Management Information Systems", "graduation_year": 2022},
    {"full_name": "Priscilla Otoo", "school_name": "Central University", "degree": "BA Theology", "graduation_year": 2019},
    {"full_name": "Emmanuel Tetteh", "school_name": "Central University", "degree": "BSc Accounting", "graduation_year": 2020},
    {"full_name": "Gifty Lartey", "school_name": "Central University", "degree": "BA Marketing", "graduation_year": 2021},
    {"full_name": "Richard Odame", "school_name": "GIMPA", "degree": "BSc Public Administration", "graduation_year": 2018},
    {"full_name": "Linda Ansah", "school_name": "GIMPA", "degree": "BSc Human Resource Management", "graduation_year": 2020},
    {"full_name": "Solomon Bruce", "school_name": "GIMPA", "degree": "LLB Law", "graduation_year": 2022},
]


def upgrade() -> None:
    op.add_column("verification_logs", sa.Column("response_data", postgresql.JSONB, nullable=True))

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
    op.execute(
        "DELETE FROM verified_schools WHERE school_name IN ("
        "'University of Education, Winneba', 'University for Development Studies', "
        "'Ashesi University', 'Central University', 'GIMPA')"
    )
    op.drop_column("verification_logs", "response_data")
