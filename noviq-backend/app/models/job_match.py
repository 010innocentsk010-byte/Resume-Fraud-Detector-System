import uuid

from sqlalchemy import CheckConstraint, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin


class JobMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_matches"
    __table_args__ = (
        CheckConstraint(
            "(job_description_id IS NOT NULL) != (job_posting_id IS NOT NULL)",
            name="ck_job_match_exactly_one_parent",
        ),
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    resume: Mapped["Resume"] = relationship()

    # Exactly one of job_description_id / job_posting_id is set (enforced by
    # ck_job_match_exactly_one_parent) — a match either scores a resume
    # against an ad-hoc JobDescription (Rank candidates, one-off matching) or
    # against a durable, publicly link-shared JobPosting (an Application).
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=True
    )
    job_description: Mapped["JobDescription | None"] = relationship(back_populates="matches")

    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    job_posting: Mapped["JobPosting | None"] = relationship()

    # 0-100, higher = better match (opposite semantics of Analysis's suspicion scores)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    matched_skills: Mapped[list] = mapped_column(JSONB, default=list)
    missing_skills: Mapped[list] = mapped_column(JSONB, default=list)
    semantic_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
