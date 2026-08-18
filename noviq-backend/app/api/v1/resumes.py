import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.applicant import Applicant
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.schemas.analysis import AnalysisRead
from app.schemas.resume import ParsedResume, ResumeDetail, ResumeRead
from app.services.analysis_engine import run_analysis
from app.services.resume_intake import find_or_create_applicant, intake_and_analyze_resume

router = APIRouter(tags=["Resumes"])


def _to_resume_detail(resume: Resume) -> ResumeDetail:
    return ResumeDetail(
        id=resume.id,
        applicant_id=resume.applicant_id,
        original_filename=resume.original_filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        status=resume.status,
        created_at=resume.created_at,
        parsed_data=ParsedResume.model_validate(resume.parsed_data) if resume.parsed_data else None,
    )


@router.post("/resumes/upload", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
def upload_resume_direct(
    name: str = Form(min_length=2, max_length=255),
    email: EmailStr = Form(),
    phone: str | None = Form(default=None),
    field_of_study: str | None = Form(default=None),
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeDetail:
    """One-step recruiter upload: takes the candidate's contact details and
    resume together, finds or creates their Applicant record, and runs the
    same intake pipeline as every other resume path — no separate
    "create a candidate first" step. Mirrors the public apply flow's
    find-or-create behavior, just authenticated and recruiter-attributed.
    """
    applicant = find_or_create_applicant(db, name, str(email), phone, field_of_study, created_by_id=current_user.id)
    resume = intake_and_analyze_resume(db, applicant, file, uploaded_by_id=current_user.id)
    return _to_resume_detail(resume)


@router.post("/applicants/{applicant_id}/resumes", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
def upload_resume(
    applicant_id: uuid.UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeDetail:
    applicant = db.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")

    resume = intake_and_analyze_resume(db, applicant, file, uploaded_by_id=current_user.id)
    return _to_resume_detail(resume)


@router.get("/applicants/{applicant_id}/resumes", response_model=list[ResumeRead])
def list_applicant_resumes(
    applicant_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Resume]:
    applicant = db.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")
    return sorted(applicant.resumes, key=lambda r: r.created_at, reverse=True)


@router.get("/resumes/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeDetail:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return _to_resume_detail(resume)


@router.post("/resumes/{resume_id}/analyze", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
def analyze_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisRead:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if resume.status not in (ResumeStatus.PARSED, ResumeStatus.ANALYZED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Resume is not ready for analysis (status={resume.status.value})",
        )

    try:
        analysis = run_analysis(db, resume)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return AnalysisRead.model_validate(analysis)
