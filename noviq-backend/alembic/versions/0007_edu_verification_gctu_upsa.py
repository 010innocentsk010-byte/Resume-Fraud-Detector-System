"""education verification: seed GCTU and UPSA

Revision ID: 0007_edu_verification_v3
Revises: 0006_edu_verification_v2
Create Date: 2026-08-10

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_edu_verification_v3"
down_revision: Union[str, None] = "0006_edu_verification_v2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fictional demo records only — not real students or alumni.
SEED_SCHOOLS = [
    {"full_name": "Nii Armah Quaye", "school_name": "Ghana Communication Technology University", "degree": "BSc Telecommunications Engineering", "graduation_year": 2021},
    {"full_name": "Belinda Osei", "school_name": "Ghana Communication Technology University", "degree": "BSc Computer Science", "graduation_year": 2019},
    {"full_name": "Prosper Yeboah", "school_name": "Ghana Communication Technology University", "degree": "BSc Information Technology", "graduation_year": 2022},
    {"full_name": "Rebecca Amoako", "school_name": "University of Professional Studies, Accra", "degree": "BSc Accounting", "graduation_year": 2020},
    {"full_name": "Dennis Kwarteng", "school_name": "University of Professional Studies, Accra", "degree": "BSc Marketing", "graduation_year": 2018},
    {"full_name": "Joyce Nyarko", "school_name": "University of Professional Studies, Accra", "degree": "BSc Human Resource Management", "graduation_year": 2023},
]


def upgrade() -> None:
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
        "'Ghana Communication Technology University', 'University of Professional Studies, Accra')"
    )
