import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.analysis import RiskLevel


class ApplicantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: str | None = None
    field_of_study: str | None = None


class ApplicantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    field_of_study: str | None = None
    created_at: datetime
    resume_count: int = 0
    latest_resume_id: uuid.UUID | None = None
    latest_fraud_score: float | None = None
    latest_risk_level: RiskLevel | None = None
    latest_flag_count: int | None = None
