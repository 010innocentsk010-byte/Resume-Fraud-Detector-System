import uuid

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin


class JobMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_matches"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    resume: Mapped["Resume"] = relationship()

    job_description_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    job_description: Mapped["JobDescription"] = relationship(back_populates="matches")

    # 0-100, higher = better match (opposite semantics of Analysis's suspicion scores)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    matched_skills: Mapped[list] = mapped_column(JSONB, default=list)
    missing_skills: Mapped[list] = mapped_column(JSONB, default=list)
    semantic_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
