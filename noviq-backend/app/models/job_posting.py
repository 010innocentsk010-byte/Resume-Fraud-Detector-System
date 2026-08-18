import enum
import secrets
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum


class JobPostingStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


def _generate_public_token() -> str:
    return secrets.token_urlsafe(32)


class JobPosting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A recruiter-authored job opening with a public, unauthenticated apply
    link. Deliberately separate from JobDescription (a throwaway scoring
    input with no lifecycle) — this is a durable, publicly link-shared
    posting with its own status and an applications inbox."""

    __tablename__ = "job_postings"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    career_field: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_skills: Mapped[list] = mapped_column(JSONB, default=list)

    status: Mapped[JobPostingStatus] = mapped_column(
        str_enum(JobPostingStatus, "job_posting_status"), default=JobPostingStatus.DRAFT, nullable=False
    )
    # Public URL identifier, decoupled from the primary key so a link can be
    # rotated (e.g. if pasted somewhere by mistake) without touching FKs.
    public_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, default=_generate_public_token
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    applications: Mapped[list["Application"]] = relationship(
        back_populates="job_posting", cascade="all, delete-orphan"
    )
