import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.applicant import Applicant
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.schemas.job_match import (
    CandidateRankingEntry,
    JobDescriptionCreate,
    JobDescriptionRead,
    JobMatchRead,
    JobMatchRequest,
)
from app.services.job_match import analyze_job_match, analyze_job_match_batch, build_match_recommendation
from app.services.resume_parser import extract_skills

router = APIRouter(tags=["Job Match"])


@router.post("/job-descriptions", response_model=JobDescriptionRead, status_code=status.HTTP_201_CREATED)
def create_job_description(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescription:
    job_description = JobDescription(
        title=payload.title,
        company=payload.company,
        career_field=payload.career_field,
        raw_text=payload.raw_text,
        parsed_skills=extract_skills(payload.raw_text),
        created_by_id=current_user.id,
    )
    db.add(job_description)
    db.commit()
    db.refresh(job_description)
    return job_description


@router.get("/job-descriptions", response_model=list[JobDescriptionRead])
def list_job_descriptions(
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JobDescription]:
    stmt = select(JobDescription).order_by(JobDescription.created_at.desc())
    if q:
        stmt = stmt.where(JobDescription.title.ilike(f"%{q}%"))
    return list(db.scalars(stmt).all())


@router.get("/job-descriptions/{job_description_id}", response_model=JobDescriptionRead)
def get_job_description(
    job_description_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescription:
    job_description = db.get(JobDescription, job_description_id)
    if not job_description:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return job_description


@router.get("/job-descriptions/{job_description_id}/candidate-ranking", response_model=list[CandidateRankingEntry])
def rank_candidates_for_job(
    job_description_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CandidateRankingEntry]:
    """Ranks every candidate's most recently analyzed resume against a job
    description. Computed on the fly — not persisted as JobMatch rows.
    """
    job_description = db.get(JobDescription, job_description_id)
    if not job_description:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    applicants = db.scalars(select(Applicant)).all()
    candidates: list[tuple[Applicant, Resume]] = []
    for applicant in applicants:
        resume = db.scalar(
            select(Resume)
            .where(Resume.applicant_id == applicant.id, Resume.status == ResumeStatus.ANALYZED)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        if resume:
            candidates.append((applicant, resume))

    if not candidates:
        return []

    match_results = analyze_job_match_batch([resume for _, resume in candidates], job_description.raw_text)

    entries: list[CandidateRankingEntry] = []
    for (applicant, resume), match in zip(candidates, match_results):
        analysis = db.scalar(
            select(Analysis).where(Analysis.resume_id == resume.id).order_by(Analysis.created_at.desc()).limit(1)
        )
        entries.append(
            CandidateRankingEntry(
                applicant_id=applicant.id,
                applicant_name=applicant.name,
                applicant_email=applicant.email,
                resume_id=resume.id,
                match_score=match.match_score,
                matched_skills=match.matched_skills,
                missing_skills=match.missing_skills,
                recommendation=build_match_recommendation(match.match_score),
                fraud_score=analysis.fraud_score if analysis else None,
                risk_level=analysis.risk_level if analysis else None,
                ats_score=analysis.ats_score if analysis else None,
            )
        )

    entries.sort(key=lambda e: e.match_score, reverse=True)
    return entries[:limit]


@router.post("/resumes/{resume_id}/job-match", response_model=JobMatchRead, status_code=status.HTTP_201_CREATED)
def match_resume_to_job(
    resume_id: uuid.UUID,
    payload: JobMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobMatch:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if resume.status not in (ResumeStatus.PARSED, ResumeStatus.ANALYZED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Resume is not ready for job matching (status={resume.status.value})",
        )

    if payload.job_description_id is not None:
        job_description = db.get(JobDescription, payload.job_description_id)
        if not job_description:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    else:
        job_description = JobDescription(
            title=payload.title or "Untitled job description",
            company=payload.company,
            career_field=payload.career_field,
            raw_text=payload.job_description_text or "",
            parsed_skills=extract_skills(payload.job_description_text or ""),
            created_by_id=current_user.id,
        )
        db.add(job_description)
        db.flush()

    result = analyze_job_match(resume, job_description.raw_text)

    job_match = JobMatch(
        resume_id=resume.id,
        job_description_id=job_description.id,
        match_score=result.match_score,
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
        semantic_similarity=result.semantic_similarity,
        details=result.details,
    )
    db.add(job_match)
    db.commit()
    db.refresh(job_match)
    return job_match


@router.get("/resumes/{resume_id}/job-matches", response_model=list[JobMatchRead])
def list_job_matches_for_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JobMatch]:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    stmt = select(JobMatch).where(JobMatch.resume_id == resume_id).order_by(JobMatch.created_at.desc())
    return list(db.scalars(stmt).all())
