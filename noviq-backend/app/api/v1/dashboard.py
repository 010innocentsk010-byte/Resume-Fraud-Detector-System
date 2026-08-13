from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis, RiskLevel
from app.models.applicant import Applicant
from app.models.resume import Resume
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAnalytics,
    DashboardSummary,
    FlagCategoryCount,
    RiskDistributionPoint,
    TrendPoint,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

AI_FLAG_THRESHOLD = 50.0


def _latest_analyses(db: Session) -> list[Analysis]:
    """One Analysis per resume — the most recent run for each."""
    subquery = (
        select(Analysis.resume_id, func.max(Analysis.created_at).label("latest"))
        .group_by(Analysis.resume_id)
        .subquery()
    )
    stmt = select(Analysis).join(
        subquery,
        (Analysis.resume_id == subquery.c.resume_id) & (Analysis.created_at == subquery.c.latest),
    )
    return list(db.scalars(stmt).all())


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardSummary:
    total_applicants = db.scalar(select(func.count()).select_from(Applicant)) or 0
    total_resumes = db.scalar(select(func.count()).select_from(Resume)) or 0

    analyses = _latest_analyses(db)
    high = sum(1 for a in analyses if a.risk_level == RiskLevel.HIGH)
    medium = sum(1 for a in analyses if a.risk_level == RiskLevel.MEDIUM)
    low = sum(1 for a in analyses if a.risk_level == RiskLevel.LOW)
    verified = low
    ai_flagged = sum(1 for a in analyses if a.ai_score >= AI_FLAG_THRESHOLD)
    avg_score = round(sum(a.fraud_score for a in analyses) / len(analyses), 1) if analyses else 0.0
    ai_rate = round((ai_flagged / len(analyses)) * 100, 1) if analyses else 0.0

    return DashboardSummary(
        total_applicants=total_applicants,
        total_resumes=total_resumes,
        verified_candidates=verified,
        high_risk_candidates=high,
        medium_risk_candidates=medium,
        low_risk_candidates=low,
        ai_detection_rate=ai_rate,
        average_fraud_score=avg_score,
    )


@router.get("/analytics", response_model=DashboardAnalytics)
def get_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardAnalytics:
    summary = get_summary(db, current_user)
    analyses = _latest_analyses(db)

    risk_distribution = [
        RiskDistributionPoint(label="Low", count=summary.low_risk_candidates),
        RiskDistributionPoint(label="Medium", count=summary.medium_risk_candidates),
        RiskDistributionPoint(label="High", count=summary.high_risk_candidates),
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    by_day: dict[str, list[float]] = defaultdict(list)
    for a in analyses:
        created = a.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created >= cutoff:
            by_day[created.strftime("%Y-%m-%d")].append(a.fraud_score)

    fraud_trend = [
        TrendPoint(date=day, average_fraud_score=round(sum(scores) / len(scores), 1), count=len(scores))
        for day, scores in sorted(by_day.items())
    ]

    category_counter: Counter[str] = Counter()
    for a in analyses:
        for flag in a.flags or []:
            category_counter[flag.get("category", "unknown")] += 1
    top_flag_categories = [
        FlagCategoryCount(category=cat, count=count) for cat, count in category_counter.most_common(10)
    ]

    return DashboardAnalytics(
        summary=summary,
        risk_distribution=risk_distribution,
        fraud_trend=fraud_trend,
        top_flag_categories=top_flag_categories,
    )
