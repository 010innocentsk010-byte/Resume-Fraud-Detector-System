import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Applicant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applicants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by: Mapped["User"] = relationship(back_populates="applicants")

    resumes: Mapped[list["Resume"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    verification_logs: Mapped[list["VerificationLog"]] = relationship(
        back_populates="applicant", cascade="all, delete-orphan"
    )
