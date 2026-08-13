from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_applicants: int
    total_resumes: int
    verified_candidates: int
    high_risk_candidates: int
    medium_risk_candidates: int
    low_risk_candidates: int
    ai_detection_rate: float  # percentage of analyzed resumes flagged as likely AI-generated
    average_fraud_score: float


class RiskDistributionPoint(BaseModel):
    label: str
    count: int


class TrendPoint(BaseModel):
    date: str
    average_fraud_score: float
    count: int


class FlagCategoryCount(BaseModel):
    category: str
    count: int


class DashboardAnalytics(BaseModel):
    summary: DashboardSummary
    risk_distribution: list[RiskDistributionPoint]
    fraud_trend: list[TrendPoint]
    top_flag_categories: list[FlagCategoryCount]
