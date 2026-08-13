import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, model_validator

from app.models.analysis import RiskLevel
from app.services.job_match import build_match_recommendation


class JobDescriptionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    company: str | None = None
    career_field: str | None = None
    raw_text: str = Field(min_length=20)


class JobDescriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None
    career_field: str | None = None
    raw_text: str
    parsed_skills: list[str]
    created_at: datetime


class JobMatchRequest(BaseModel):
    job_description_id: uuid.UUID | None = None
    job_description_text: str | None = None
    title: str | None = None
    company: str | None = None
    career_field: str | None = None

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "JobMatchRequest":
        has_id = self.job_description_id is not None
        has_text = bool(self.job_description_text and self.job_description_text.strip())
        if has_id == has_text:
            raise ValueError("Provide exactly one of job_description_id or job_description_text")
        return self


class JobMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    job_description_id: uuid.UUID
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    semantic_similarity: float
    details: dict[str, Any]
    created_at: datetime
    job_description: JobDescriptionRead | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def recommendation(self) -> str:
        return build_match_recommendation(self.match_score)


class CandidateRankingEntry(BaseModel):
    applicant_id: uuid.UUID
    applicant_name: str
    applicant_email: EmailStr
    resume_id: uuid.UUID
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    recommendation: str
    fraud_score: float | None
    risk_level: RiskLevel | None
    ats_score: float | None
