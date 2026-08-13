"""Seeds a default admin account for first login.

Run with: python -m app.db.seed
"""
from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole

configure_logging()
logger = get_logger(__name__)

DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "ChangeMe123!"


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
        if existing:
            logger.info("Admin account already exists (%s); skipping seed.", DEFAULT_ADMIN_EMAIL)
            return

        admin = User(
            name="System Administrator",
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Seeded default admin account: %s / %s (change this password immediately)", DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
