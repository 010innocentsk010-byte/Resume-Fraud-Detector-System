from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import RateLimitExceededError, enforce_rate_limit
from app.db.session import get_db
from app.models.applicant import Applicant
from app.models.user import User
from app.schemas.education_verification import (
    EducationVerifyFromEvidenceRequest,
    EducationVerifyRequest,
    EducationVerifyResponse,
)
from app.services.education_evidence_extraction import (
    EvidenceExtractionError,
    EvidenceExtractionNotConfiguredError,
    EvidenceExtractionProviderError,
)
from app.services.education_verification import verify_education, verify_education_from_evidence

router = APIRouter(prefix="/education", tags=["Education Verification"])


@router.post("/verify", response_model=EducationVerifyResponse)
def verify_education_endpoint(
    payload: EducationVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EducationVerifyResponse:
    if not payload.candidate_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate consent is required before verifying education history.",
        )

    applicant = db.get(Applicant, payload.candidate_id)
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    try:
        enforce_rate_limit(str(current_user.id), settings.EDUCATION_VERIFY_RATE_LIMIT_PER_MINUTE)
    except RateLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    return verify_education(
        db=db,
        applicant_id=payload.candidate_id,
        requested_by_id=current_user.id,
        full_name=payload.full_name,
        school_name=payload.school_name,
        degree=payload.degree,
        graduation_year=payload.graduation_year,
        candidate_consent=payload.candidate_consent,
    )


@router.post("/verify-from-evidence", response_model=EducationVerifyResponse)
def verify_education_from_evidence_endpoint(
    payload: EducationVerifyFromEvidenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EducationVerifyResponse:
    """Same claim as /verify, but checked against a pasted/uploaded evidence
    document instead of the local DB or Ghana registry API. An LLM only
    extracts literal fields from the document (see
    education_evidence_extraction.py); the VERIFIED/NOT_FOUND/PENDING call is
    made by deterministic code in verify_education_from_evidence()."""
    if not payload.candidate_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate consent is required before verifying education history.",
        )

    applicant = db.get(Applicant, payload.candidate_id)
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    try:
        enforce_rate_limit(str(current_user.id), settings.EDUCATION_VERIFY_RATE_LIMIT_PER_MINUTE)
    except RateLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    try:
        return verify_education_from_evidence(
            db=db,
            applicant_id=payload.candidate_id,
            requested_by_id=current_user.id,
            full_name=payload.full_name,
            school_name=payload.school_name,
            degree=payload.degree,
            graduation_year=payload.graduation_year,
            candidate_consent=payload.candidate_consent,
            evidence_text=payload.evidence_text,
        )
    except EvidenceExtractionNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except EvidenceExtractionProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except EvidenceExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
