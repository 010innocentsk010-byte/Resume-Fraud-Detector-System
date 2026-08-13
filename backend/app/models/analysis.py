import enum
import uuid

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analysis"

    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    resume: Mapped["Resume"] = relationship(back_populates="analyses")

    # Component scores, each 0-100 (higher = more suspicious)
    experience_score: Mapped[float] = mapped_column(Float, default=0.0)
    education_score: Mapped[float] = mapped_column(Float, default=0.0)
    skill_score: Mapped[float] = mapped_column(Float, default=0.0)
    formatting_score: Mapped[float] = mapped_column(Float, default=0.0)
    timeline_score: Mapped[float] = mapped_column(Float, default=0.0)
    ai_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_stuffing_score: Mapped[float] = mapped_column(Float, default=0.0)
    duplicate_score: Mapped[float] = mapped_column(Float, default=0.0)

    fraud_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[RiskLevel] = mapped_column(str_enum(RiskLevel, "risk_level"), default=RiskLevel.LOW)

    # List[{category, severity, title, message, evidence}]
    flags: Mapped[list] = mapped_column(JSONB, default=list)
    # Free-form breakdown used by the dashboard/report (weights, sub-signals, similar resumes, etc.)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    # --- ATS / AI-section signals (parallel to fraud scoring above, not part of it) ---
    # 0-100, higher = MORE ATS-friendly (inverse semantics vs. the suspicion scores above)
    ats_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    ats_issues: Mapped[list] = mapped_column(JSONB, default=list)
    # List[{section, ai_confidence, signals}]
    ai_section_scores: Mapped[list] = mapped_column(JSONB, default=list)

    reports: Mapped[list["Report"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
