import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.job_posting import JobPostingStatus


class JobPostingCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    company: str | None = None
    career_field: str | None = None
    location: str | None = None
    raw_text: str = Field(min_length=20)


class JobPostingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    company: str | None = None
    career_field: str | None = None
    location: str | None = None
    raw_text: str | None = Field(default=None, min_length=20)


class JobPostingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None
    career_field: str | None
    location: str | None
    raw_text: str
    parsed_skills: list[str]
    status: JobPostingStatus
    public_token: str
    published_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    application_count: int = 0


class PublicJobPostingRead(BaseModel):
    """Public-safe view rendered on the unauthenticated apply page — no
    internal id, owner, or token echoed back."""

    title: str
    company: str | None
    career_field: str | None
    location: str | None
    description: str
    parsed_skills: list[str]
    status: JobPostingStatus


class PublicApplyResponse(BaseModel):
    """Deliberately minimal: no application_id, resume_id, fraud_score, or
    risk_level. Candidates must never see their own fraud-screening data —
    this schema has no field capable of carrying it."""

    message: str
    submitted_at: datetime
