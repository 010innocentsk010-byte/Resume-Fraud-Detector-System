"""Aggregates the individual fraud-detection signals into a single 0-100
fraud risk score with a risk level and human-readable recommendation.

Weights approximate the target distribution (experience/education/skills/
formatting/timeline/AI ~15/20/30/10/15/10) while also incorporating
keyword-stuffing and duplicate-detection as first-class signals baked
into the skills and formatting axes respectively.
"""
from dataclasses import dataclass

from app.models.analysis import RiskLevel
from app.schemas.analysis import FraudFlag

WEIGHTS = {
    "experience_score": 0.15,
    "education_score": 0.15,
    "skill_score": 0.20,
    "keyword_stuffing_score": 0.10,
    "formatting_score": 0.10,
    "timeline_score": 0.15,
    "ai_score": 0.10,
    "duplicate_score": 0.05,
}

HIGH_RISK_THRESHOLD = 65
MEDIUM_RISK_THRESHOLD = 35


@dataclass
class ComponentScores:
    experience_score: float = 0.0
    education_score: float = 0.0
    skill_score: float = 0.0
    keyword_stuffing_score: float = 0.0
    formatting_score: float = 0.0
    timeline_score: float = 0.0
    ai_score: float = 0.0
    duplicate_score: float = 0.0


def compute_fraud_score(scores: ComponentScores) -> float:
    total = sum(getattr(scores, field) * weight for field, weight in WEIGHTS.items())
    return round(min(100.0, max(0.0, total)), 1)


def classify_risk(fraud_score: float) -> RiskLevel:
    if fraud_score >= HIGH_RISK_THRESHOLD:
        return RiskLevel.HIGH
    if fraud_score >= MEDIUM_RISK_THRESHOLD:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def build_recommendation(fraud_score: float, risk_level: RiskLevel, flags: list[FraudFlag]) -> str:
    high_severity = [f for f in flags if f.severity == "high"]
    categories = sorted({f.category.replace("_", " ") for f in flags})

    if risk_level == RiskLevel.HIGH:
        headline = (
            f"High fraud risk ({fraud_score:.0f}/100). Manual verification is strongly "
            "recommended before proceeding with this candidate."
        )
    elif risk_level == RiskLevel.MEDIUM:
        headline = (
            f"Medium fraud risk ({fraud_score:.0f}/100). Some claims warrant a closer look "
            "during screening or the interview."
        )
    else:
        headline = (
            f"Low fraud risk ({fraud_score:.0f}/100). No significant red flags were detected, "
            "though this does not replace standard reference checks."
        )

    if not flags:
        return headline + " No specific issues were flagged."

    detail = f" Flagged areas: {', '.join(categories)}."
    if high_severity:
        detail += (
            f" {len(high_severity)} high-severity issue(s) should be discussed directly with "
            "the candidate: " + "; ".join(f.title for f in high_severity[:3]) + "."
        )
    return headline + detail
