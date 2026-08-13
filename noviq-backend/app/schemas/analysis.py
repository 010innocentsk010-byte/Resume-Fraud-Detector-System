import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, computed_field

from app.models.analysis import RiskLevel


class FraudFlag(BaseModel):
    category: str
    severity: str  # "low" | "medium" | "high"
    title: str
    message: str
    evidence: list[str] = []


class SectionAIScore(BaseModel):
    section: str
    ai_confidence: float  # 0-100, higher = more likely AI-written
    signals: list[str]


# The set of categories every analysis actually checks. A category with no flag
# attached to it means that check passed clean — used to render "consistent"
# checkmarks alongside the negative flags, not just silence.
CHECK_CATEGORIES: dict[str, str] = {
    "timeline": "Employment timeline",
    "education": "Education history",
    "skills": "Skills authenticity",
    "keyword_stuffing": "Keyword usage",
    "formatting": "Document formatting",
    "ai_generated": "Writing originality",
    "duplicate": "Duplicate submission",
}


class ConsistencyCheck(BaseModel):
    category: str
    label: str
    passed: bool


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    experience_score: float
    education_score: float
    skill_score: float
    formatting_score: float
    timeline_score: float
    ai_score: float
    keyword_stuffing_score: float
    duplicate_score: float
    fraud_score: float
    risk_level: RiskLevel
    flags: list[FraudFlag]
    details: dict[str, Any]
    ats_score: float
    ats_issues: list[FraudFlag]
    ai_section_scores: list[SectionAIScore]
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def consistency_checks(self) -> list[ConsistencyCheck]:
        flagged_categories = {flag.category for flag in self.flags}
        return [
            ConsistencyCheck(category=category, label=label, passed=category not in flagged_categories)
            for category, label in CHECK_CATEGORIES.items()
        ]
