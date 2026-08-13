import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum


class VerificationStatus(str, enum.Enum):
    VERIFIED = "verified"
    NOT_FOUND = "not_found"
    PENDING = "pending"
    ERROR = "error"


class VerificationSource(str, enum.Enum):
    LOCAL_DB = "local_db"
    GHANA_API = "ghana_api"
    DOCUMENT_EVIDENCE = "document_evidence"


class VerifiedSchool(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Local mock ground-truth table standing in for a real registry lookup.

    Swap-out point: once a real external provider is confirmed, this table
    keeps serving as the fast-path cache in front of it.
    """

    __tablename__ = "verified_schools"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    school_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)


class VerificationLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "verification_logs"

    applicant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applicants.id"), nullable=False)
    applicant: Mapped["Applicant"] = relationship()

    requested_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    school_name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)

    candidate_consent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[VerificationStatus] = mapped_column(str_enum(VerificationStatus, "verification_status"), nullable=False)
    verified_by: Mapped[VerificationSource | None] = mapped_column(
        str_enum(VerificationSource, "verification_source"), nullable=True
    )
    # Raw payload from the external provider call (audit/debugging only — never
    # populated for local-DB matches or when no external call was made).
    response_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
