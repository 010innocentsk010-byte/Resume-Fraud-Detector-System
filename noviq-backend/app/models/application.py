import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum


class ApplicationStatus(str, enum.Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"


class ApplicationSource(str, enum.Enum):
    PUBLIC_LINK = "public_link"
    MANUAL = "manual"


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A candidate's application to a specific JobPosting — the recruiter
    pipeline entity linking a posting, an applicant, their resume, and the
    resulting job-match score, plus a recruiter-managed workflow status."""

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_posting_id", "applicant_id", name="uq_application_posting_applicant"),
    )

    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_posting: Mapped["JobPosting"] = relationship(back_populates="applications")

    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    applicant: Mapped["Applicant"] = relationship()

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    resume: Mapped["Resume"] = relationship()

    # Nullable: job-match scoring is best-effort/non-fatal, same tolerance
    # the fraud-analysis step already has — a scoring hiccup must not block
    # the application from landing in the recruiter's pipeline.
    job_match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_matches.id"), nullable=True
    )
    job_match: Mapped["JobMatch | None"] = relationship()

    status: Mapped[ApplicationStatus] = mapped_column(
        str_enum(ApplicationStatus, "application_status"), default=ApplicationStatus.NEW, nullable=False, index=True
    )
    source: Mapped[ApplicationSource] = mapped_column(str_enum(ApplicationSource, "application_source"), nullable=False)

    # Null = not yet computed (mirrors job_match_id's tolerance for a scoring
    # hiccup). Computed once at application-creation time from the same
    # match-score + fraud-risk signals already on this application — not
    # re-evaluated later, same "not retroactive" precedent as posting edits.
    qualified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
