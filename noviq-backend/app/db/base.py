# Imported by Alembic's env.py so Base.metadata is aware of every model
# before autogenerate diffs the database.
from app.db.base_class import Base  # noqa: F401
from app.models import (  # noqa: F401
    Analysis,
    Applicant,
    Application,
    JobDescription,
    JobMatch,
    JobPosting,
    Report,
    RevokedRefreshToken,
    Resume,
    User,
)
