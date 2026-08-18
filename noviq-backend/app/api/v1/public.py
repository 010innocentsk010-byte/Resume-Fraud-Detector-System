"""Public, unauthenticated surface for the job-posting apply-link flow.

No endpoint in this file depends on get_current_user — keeping every public
route in one dedicated file makes "is anything here missing auth" trivial
to audit (nothing here should ever have it).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.rate_limit import RateLimitExceededError, enforce_rate_limit
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.application import Application, ApplicationSource, ApplicationStatus
from app.models.job_match import JobMatch
from app.models.job_posting import JobPosting, JobPostingStatus
from app.schemas.job_posting import PublicApplyResponse, PublicJobPostingRead
from app.services.email_notifications import send_qualification_email
from app.services.job_match import analyze_job_match, is_qualified
from app.services.resume_intake import find_or_create_applicant, intake_and_analyze_resume

router = APIRouter(prefix="/public", tags=["Public"])
logger = get_logger(__name__)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _get_published_posting(db: Session, token: str) -> JobPosting:
    posting = db.scalar(select(JobPosting).where(JobPosting.public_token == token))
    # Draft postings 404 rather than reveal existence, even to someone who
    # somehow has the token — a recruiter previews drafts from the
    # authenticated recruiter UI, never through this public endpoint.
    if not posting or posting.status == JobPostingStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
    return posting


@router.get("/postings/{token}", response_model=PublicJobPostingRead)
def get_public_posting(token: str, request: Request, db: Session = Depends(get_db)) -> PublicJobPostingRead:
    try:
        enforce_rate_limit(f"public_view:{_client_ip(request)}", settings.PUBLIC_VIEW_RATE_LIMIT_PER_MINUTE, 60)
    except RateLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    posting = _get_published_posting(db, token)
    return PublicJobPostingRead(
        title=posting.title,
        company=posting.company,
        career_field=posting.career_field,
        location=posting.location,
        description=posting.raw_text,
        parsed_skills=posting.parsed_skills,
        status=posting.status,
    )


@router.post("/postings/{token}/apply", response_model=PublicApplyResponse, status_code=status.HTTP_201_CREATED)
def apply_to_posting(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    name: str = Form(min_length=2, max_length=255),
    email: EmailStr = Form(),
    phone: str | None = Form(default=None),
    field_of_study: str | None = Form(default=None),
    file: UploadFile = File(),
    db: Session = Depends(get_db),
) -> PublicApplyResponse:
    try:
        enforce_rate_limit(f"public_apply:{_client_ip(request)}", settings.PUBLIC_APPLY_RATE_LIMIT_PER_HOUR, 3600)
    except RateLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    posting = _get_published_posting(db, token)
    if posting.status == JobPostingStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This job posting is no longer accepting applications")

    applicant = find_or_create_applicant(db, name, str(email), phone, field_of_study, created_by_id=None)

    existing = db.scalar(
        select(Application).where(Application.job_posting_id == posting.id, Application.applicant_id == applicant.id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already applied to this position")

    # Raises HTTPException (415/413/400/422) on invalid/unparseable files —
    # the exact same validation the authenticated recruiter upload uses.
    resume = intake_and_analyze_resume(db, applicant, file, uploaded_by_id=None)

    job_match_id = None
    try:
        result = analyze_job_match(resume, posting.raw_text)
        job_match = JobMatch(
            resume_id=resume.id,
            job_posting_id=posting.id,
            match_score=result.match_score,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            semantic_similarity=result.semantic_similarity,
            details=result.details,
        )
        db.add(job_match)
        db.flush()
        job_match_id = job_match.id
    except Exception:
        # A scoring hiccup must not block the application from landing in
        # the recruiter's pipeline — same tolerance intake already has for
        # fraud analysis.
        logger.exception("Job-match scoring failed for resume %s against posting %s", resume.id, posting.id)

    match_score = None
    if job_match_id is not None:
        job_match = db.get(JobMatch, job_match_id)
        match_score = job_match.match_score if job_match else None
    analysis = db.scalar(
        select(Analysis).where(Analysis.resume_id == resume.id).order_by(Analysis.created_at.desc()).limit(1)
    )
    qualified = is_qualified(match_score, analysis.risk_level) if match_score is not None and analysis else None

    application = Application(
        job_posting_id=posting.id,
        applicant_id=applicant.id,
        resume_id=resume.id,
        job_match_id=job_match_id,
        status=ApplicationStatus.NEW,
        source=ApplicationSource.PUBLIC_LINK,
        qualified=qualified,
    )
    db.add(application)
    db.commit()

    if qualified is not None:
        background_tasks.add_task(
            send_qualification_email, applicant.email, applicant.name, posting.title, posting.company, qualified
        )

    return PublicApplyResponse(
        message="Your application has been received.",
        submitted_at=datetime.now(timezone.utc),
    )
