import enum
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum


class ResumeFileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"


class ResumeStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    applicant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applicants.id"), nullable=False)
    applicant: Mapped["Applicant"] = relationship(back_populates="resumes")

    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[ResumeFileType] = mapped_column(str_enum(ResumeFileType, "resume_file_type"), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[ResumeStatus] = mapped_column(
        str_enum(ResumeStatus, "resume_status"), default=ResumeStatus.UPLOADED, nullable=False
    )

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    text_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
