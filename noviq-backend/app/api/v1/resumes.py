import uuid
import zipfile
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.applicant import Applicant
from app.models.resume import Resume, ResumeFileType, ResumeStatus
from app.models.user import User
from app.schemas.analysis import AnalysisRead
from app.schemas.resume import ParsedResume, ResumeDetail, ResumeRead
from app.services.analysis_engine import run_analysis
from app.services.fraud.duplicate_detection import compute_fingerprint
from app.services.resume_parser import parse_resume_text
from app.services.storage import get_storage
from app.services.text_extraction import UnsupportedFileError, extract_text

router = APIRouter(tags=["Resumes"])
logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ResumeFileType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ResumeFileType.DOCX,
}


def _file_type_from_upload(file: UploadFile) -> ResumeFileType:
    if file.content_type in ALLOWED_CONTENT_TYPES:
        return ALLOWED_CONTENT_TYPES[file.content_type]
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        return ResumeFileType.PDF
    if name.endswith(".docx"):
        return ResumeFileType.DOCX
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Only PDF and DOCX resumes are supported",
    )


def _verify_file_signature(content: bytes, file_type: ResumeFileType) -> None:
    """Content-Type headers and filename extensions are client-supplied and
    trivially spoofable — check the actual file bytes match the claimed type
    before spending time parsing it."""
    if file_type == ResumeFileType.PDF:
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File content is not a valid PDF",
            )
    elif file_type == ResumeFileType.DOCX:
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("not a Word document")
        except (zipfile.BadZipFile, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File content is not a valid DOCX document",
            ) from exc


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

    file_type = _file_type_from_upload(file)
    content = file.file.read()

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit",
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    _verify_file_signature(content, file_type)

    storage = get_storage()
    storage_path = storage.save(content, file.filename or "resume")

    resume = Resume(
        applicant_id=applicant.id,
        original_filename=file.filename or "resume",
        storage_path=storage_path,
        file_type=file_type,
        file_size_bytes=len(content),
        status=ResumeStatus.UPLOADED,
        uploaded_by_id=current_user.id,
    )
    db.add(resume)
    db.flush()

    try:
        raw_text = extract_text(content, file_type.value)
        if not raw_text.strip():
            raise ValueError("No extractable text found — the file may be a scanned image without OCR support")

        parsed = parse_resume_text(raw_text)

        resume.raw_text = raw_text
        resume.parsed_data = parsed.model_dump()
        resume.text_fingerprint = compute_fingerprint(raw_text)
        resume.status = ResumeStatus.PARSED
        db.add(resume)
        db.commit()
        db.refresh(resume)
    except (UnsupportedFileError, ValueError) as exc:
        resume.status = ResumeStatus.FAILED
        db.add(resume)
        db.commit()
        logger.warning("Resume parsing failed for %s: %s", resume.id, exc)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return ResumeDetail(
        id=resume.id,
        applicant_id=resume.applicant_id,
        original_filename=resume.original_filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        status=resume.status,
        created_at=resume.created_at,
        parsed_data=ParsedResume.model_validate(resume.parsed_data),
    )


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
