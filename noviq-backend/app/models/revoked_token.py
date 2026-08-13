from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RevokedRefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Revoked refresh-token jtis, checked on every /auth/refresh so a logged-out
    (or stolen) refresh token can't be used to mint new access tokens for the
    rest of its 7-day life."""

    __tablename__ = "revoked_refresh_tokens"

    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
