import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.application import Application, ApplicationStatus
from app.models.job_match import JobMatch
from app.models.job_posting import JobPosting, JobPostingStatus
from app.models.user import User
from app.schemas.application import ApplicationRead, ApplicationUpdate
from app.schemas.job_posting import JobPostingCreate, JobPostingRead, JobPostingUpdate
from app.services.resume_parser import extract_skills

router = APIRouter(tags=["Job Postings"])


def _to_job_posting_read(db: Session, posting: JobPosting) -> JobPostingRead:
    application_count = (
        db.scalar(select(func.count()).select_from(Application).where(Application.job_posting_id == posting.id)) or 0
    )
    return JobPostingRead(
        id=posting.id,
        title=posting.title,
        company=posting.company,
        career_field=posting.career_field,
        location=posting.location,
        raw_text=posting.raw_text,
        parsed_skills=posting.parsed_skills,
        status=posting.status,
        public_token=posting.public_token,
        published_at=posting.published_at,
        closed_at=posting.closed_at,
        created_at=posting.created_at,
        application_count=application_count,
    )


def _latest_analysis_for_resume(db: Session, resume_id: uuid.UUID) -> Analysis | None:
    return db.scalar(select(Analysis).where(Analysis.resume_id == resume_id).order_by(Analysis.created_at.desc()).limit(1))


def _to_application_read(db: Session, application: Application) -> ApplicationRead:
    job_match = db.get(JobMatch, application.job_match_id) if application.job_match_id else None
    analysis = _latest_analysis_for_resume(db, application.resume_id)
    return ApplicationRead(
        id=application.id,
        job_posting_id=application.job_posting_id,
        applicant=application.applicant,
        resume_id=application.resume_id,
        status=application.status,
        source=application.source,
        created_at=application.created_at,
        match_score=job_match.match_score if job_match else None,
        matched_skills=job_match.matched_skills if job_match else [],
        missing_skills=job_match.missing_skills if job_match else [],
        fraud_score=analysis.fraud_score if analysis else None,
        risk_level=analysis.risk_level if analysis else None,
        qualified=application.qualified,
    )


def _get_posting_or_404(db: Session, posting_id: uuid.UUID) -> JobPosting:
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
    return posting


@router.post("/job-postings", response_model=JobPostingRead, status_code=status.HTTP_201_CREATED)
def create_job_posting(
    payload: JobPostingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobPostingRead:
    posting = JobPosting(
        title=payload.title,
        company=payload.company,
        career_field=payload.career_field,
        location=payload.location,
        raw_text=payload.raw_text,
        parsed_skills=extract_skills(payload.raw_text),
        created_by_id=current_user.id,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return _to_job_posting_read(db, posting)


@router.get("/job-postings", response_model=list[JobPostingRead])
def list_job_postings(
    posting_status: JobPostingStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JobPostingRead]:
    stmt = select(JobPosting).order_by(JobPosting.created_at.desc())
    if posting_status is not None:
        stmt = stmt.where(JobPosting.status == posting_status)
    postings = db.scalars(stmt).all()
    return [_to_job_posting_read(db, posting) for posting in postings]


@router.get("/job-postings/{posting_id}", response_model=JobPostingRead)
def get_job_posting(
    posting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobPostingRead:
    posting = _get_posting_or_404(db, posting_id)
    return _to_job_posting_read(db, posting)


@router.patch("/job-postings/{posting_id}", response_model=JobPostingRead)
def update_job_posting(
    posting_id: uuid.UUID,
    payload: JobPostingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobPostingRead:
    posting = _get_posting_or_404(db, posting_id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(posting, field, value)
    if "raw_text" in updates:
        # Only affects future matching — existing JobMatch/Application rows
        # are not retroactively rescored.
        posting.parsed_skills = extract_skills(posting.raw_text)

    db.add(posting)
    db.commit()
    db.refresh(posting)
    return _to_job_posting_read(db, posting)


@router.post("/job-postings/{posting_id}/publish", response_model=JobPostingRead)
def publish_job_posting(
    posting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobPostingRead:
    posting = _get_posting_or_404(db, posting_id)
    if posting.status != JobPostingStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot publish a posting with status={posting.status.value}")

    posting.status = JobPostingStatus.PUBLISHED
    posting.published_at = datetime.now(timezone.utc)
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return _to_job_posting_read(db, posting)


@router.post("/job-postings/{posting_id}/close", response_model=JobPostingRead)
def close_job_posting(
    posting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobPostingRead:
    posting = _get_posting_or_404(db, posting_id)
    if posting.status == JobPostingStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Posting is already closed")

    posting.status = JobPostingStatus.CLOSED
    posting.closed_at = datetime.now(timezone.utc)
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return _to_job_posting_read(db, posting)


@router.delete("/job-postings/{posting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_posting(
    posting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    posting = _get_posting_or_404(db, posting_id)
    application_count = (
        db.scalar(select(func.count()).select_from(Application).where(Application.job_posting_id == posting.id)) or 0
    )
    if application_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a job posting that has applications — close it instead",
        )

    db.delete(posting)
    db.commit()


@router.get("/job-postings/{posting_id}/applications", response_model=list[ApplicationRead])
def list_applications(
    posting_id: uuid.UUID,
    application_status: ApplicationStatus | None = Query(default=None, alias="status"),
    qualified: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApplicationRead]:
    _get_posting_or_404(db, posting_id)

    stmt = select(Application).where(Application.job_posting_id == posting_id)
    if application_status is not None:
        stmt = stmt.where(Application.status == application_status)
    if qualified is not None:
        stmt = stmt.where(Application.qualified == qualified)
    applications = db.scalars(stmt).all()

    entries = [_to_application_read(db, application) for application in applications]
    entries.sort(key=lambda e: (e.match_score is None, -(e.match_score or 0)))
    return entries


@router.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationRead:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application.status = payload.status
    db.add(application)
    db.commit()
    db.refresh(application)
    return _to_application_read(db, application)
