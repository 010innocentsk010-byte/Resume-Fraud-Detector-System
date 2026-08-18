"""Shared resume intake pipeline: validate the uploaded file, store it,
extract + parse text, and run fraud analysis.

Used by both the authenticated recruiter upload endpoint
(app/api/v1/resumes.py) and the public job-posting apply endpoint
(app/api/v1/public.py) — one implementation, two call sites, so the two
paths can never validate or score a resume differently.
"""
import uuid
import zipfile
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.applicant import Applicant
from app.models.resume import Resume, ResumeFileType, ResumeStatus
from app.services.analysis_engine import run_analysis
from app.services.fraud.duplicate_detection import compute_fingerprint
from app.services.resume_parser import parse_resume_text
from app.services.storage import get_storage
from app.services.text_extraction import UnsupportedFileError, extract_text

logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ResumeFileType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ResumeFileType.DOCX,
}


def file_type_from_upload(file: UploadFile) -> ResumeFileType:
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


def verify_file_signature(content: bytes, file_type: ResumeFileType) -> None:
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


def find_or_create_applicant(
    db: Session,
    name: str,
    email: str,
    phone: str | None,
    field_of_study: str | None,
    created_by_id: uuid.UUID | None,
) -> Applicant:
    """Look up an existing Applicant by (case-insensitive) email, or create
    one. Shared by every intake path that accepts a candidate's contact
    details alongside their resume — the public apply flow and the
    recruiter's direct-upload endpoint — so the same person is never split
    across two Applicant rows just because they entered through a different
    door. An existing match's name/phone/field_of_study are left as-is
    (don't let a resubmission silently overwrite recruiter-corrected data).
    """
    email_norm = email.strip().lower()
    applicant = db.scalar(select(Applicant).where(Applicant.email.ilike(email_norm)))
    if applicant is None:
        applicant = Applicant(
            name=name, email=email_norm, phone=phone, field_of_study=field_of_study, created_by_id=created_by_id
        )
        db.add(applicant)
        db.flush()
    return applicant


def intake_and_analyze_resume(
    db: Session, applicant: Applicant, file: UploadFile, uploaded_by_id: uuid.UUID | None
) -> Resume:
    """Validate, store, parse, and fraud-analyze a resume upload for the
    given applicant. Raises HTTPException (415/413/400/422) on validation or
    parsing failure. Fraud analysis is best-effort: if it fails after a
    successful parse, the resume is left at PARSED status (not FAILED) so
    the caller never loses the upload — analysis can be retried later via
    POST /resumes/{id}/analyze.

    uploaded_by_id is nullable: a resume submitted through the public
    job-posting apply flow has no recruiter uploader.
    """
    file_type = file_type_from_upload(file)
    content = file.file.read()

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit",
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    verify_file_signature(content, file_type)

    storage = get_storage()
    storage_path = storage.save(content, file.filename or "resume")

    resume = Resume(
        applicant_id=applicant.id,
        original_filename=file.filename or "resume",
        storage_path=storage_path,
        file_type=file_type,
        file_size_bytes=len(content),
        status=ResumeStatus.UPLOADED,
        uploaded_by_id=uploaded_by_id,
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

    try:
        run_analysis(db, resume)
    except Exception:
        db.rollback()
        db.refresh(resume)
        logger.exception(
            "Automatic fraud analysis failed for resume %s; left at status=%s", resume.id, resume.status.value
        )

    return resume
