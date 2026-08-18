import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.analysis import RiskLevel
from app.models.application import ApplicationSource, ApplicationStatus


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationApplicantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None = None


class ApplicationRead(BaseModel):
    id: uuid.UUID
    job_posting_id: uuid.UUID
    applicant: ApplicationApplicantSummary
    resume_id: uuid.UUID
    status: ApplicationStatus
    source: ApplicationSource
    created_at: datetime

    match_score: float | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    fraud_score: float | None = None
    risk_level: RiskLevel | None = None
    qualified: bool | None = None
