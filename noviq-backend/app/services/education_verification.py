"""Education Verification — checks a candidate's claimed school/degree/year
against a local ground-truth table first, then (if not found and a provider
key is configured) an external registry API.

Swap point: `_lookup_external` is the only place a real provider integration
lives. Replace its body to point at a different provider without touching the
router, schema, or local-DB fast path.
"""
import logging
import uuid

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.education_verification import (
    VerificationLog,
    VerificationSource,
    VerificationStatus,
    VerifiedSchool,
)
from app.schemas.education_verification import (
    EducationEvidenceExtraction,
    EducationVerifyResponse,
    VerificationDetails,
)
from app.services.education_evidence_extraction import extract_education_evidence

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    return text.strip().lower()


def _lookup_local(
    db: Session, full_name: str, school_name: str, degree: str, graduation_year: int
) -> VerifiedSchool | None:
    return db.scalar(
        select(VerifiedSchool).where(
            func.lower(VerifiedSchool.full_name) == full_name.strip().lower(),
            func.lower(VerifiedSchool.school_name) == school_name.strip().lower(),
            func.lower(VerifiedSchool.degree) == degree.strip().lower(),
            VerifiedSchool.graduation_year == graduation_year,
        )
    )


def _lookup_external(
    full_name: str, school_name: str, degree: str, graduation_year: int
) -> tuple[EducationVerifyResponse, dict | None]:
    """UNVERIFIED PROVIDER CONTRACT: settings.GHANA_EDU_API_BASE_URL has not
    been confirmed against real provider documentation. The request/response
    shape below is a placeholder — adjust it once the real API contract is
    known. Every branch below fails closed to "error"/"not_found" rather than
    raising, so a bad or unreachable provider never crashes the endpoint.

    Returns (response, raw_payload) — raw_payload is stored on the audit log
    row as-is, independent of what's returned to the caller.
    """
    try:
        response = httpx.post(
            settings.GHANA_EDU_API_BASE_URL,
            headers={"Authorization": f"Bearer {settings.GHANA_EDU_API_KEY}"},
            json={
                "full_name": full_name,
                "school_name": school_name,
                "degree": degree,
                "graduation_year": graduation_year,
            },
            timeout=settings.GHANA_EDU_API_TIMEOUT_SECONDS,
        )
    except httpx.RequestError as exc:
        logger.warning("Ghana education API unreachable: %s", exc)
        result = EducationVerifyResponse(status=VerificationStatus.ERROR, verified_by=None, details=None)
        return result, {"error": str(exc)}

    if response.status_code == 401:
        logger.error("Ghana education API rejected the configured API key (401).")
        result = EducationVerifyResponse(status=VerificationStatus.ERROR, verified_by=None, details=None)
        return result, {"status_code": 401}
    if response.status_code == 404:
        result = EducationVerifyResponse(
            status=VerificationStatus.NOT_FOUND, verified_by=VerificationSource.GHANA_API, details=None
        )
        return result, {"status_code": 404}
    if response.status_code >= 500:
        logger.error("Ghana education API returned %s.", response.status_code)
        result = EducationVerifyResponse(status=VerificationStatus.ERROR, verified_by=None, details=None)
        return result, {"status_code": response.status_code}
    if response.status_code != 200:
        logger.error("Ghana education API returned unexpected status %s.", response.status_code)
        result = EducationVerifyResponse(status=VerificationStatus.ERROR, verified_by=None, details=None)
        return result, {"status_code": response.status_code}

    try:
        payload = response.json()
    except ValueError:
        logger.error("Ghana education API returned a non-JSON response.")
        result = EducationVerifyResponse(status=VerificationStatus.ERROR, verified_by=None, details=None)
        return result, {"status_code": 200, "error": "non-JSON response body"}

    if not payload.get("found"):
        result = EducationVerifyResponse(
            status=VerificationStatus.NOT_FOUND, verified_by=VerificationSource.GHANA_API, details=None
        )
        return result, payload

    result = EducationVerifyResponse(
        status=VerificationStatus.VERIFIED,
        verified_by=VerificationSource.GHANA_API,
        details=VerificationDetails(
            school=payload.get("school_name", school_name),
            degree=payload.get("degree", degree),
            year=payload.get("graduation_year", graduation_year),
        ),
    )
    return result, payload


def _build_summary(
    full_name: str,
    school_name: str,
    degree: str,
    graduation_year: int,
    result: EducationVerifyResponse,
) -> str:
    """Deterministic, template-based HR-facing sentence — NOT an LLM call.
    Restates only fields already present on the request/response, so it can
    never assert a detail (e.g. a student ID) that verification didn't
    actually establish.
    """
    if result.status == VerificationStatus.VERIFIED and result.details:
        return (
            f"{full_name} has been verified to have attended {result.details.school}. "
            f"Records confirm completion of {result.details.degree} in {result.details.year}."
        )
    if result.status == VerificationStatus.NOT_FOUND:
        return (
            f"No record was found confirming that {full_name} attended {school_name} "
            f"for a {degree} ({graduation_year}). Manual review is recommended."
        )
    if result.status == VerificationStatus.PENDING:
        return f"Verification of {full_name}'s attendance at {school_name} is pending external confirmation."
    return (
        f"Verification of {full_name}'s attendance at {school_name} could not be completed "
        "due to a system error. Manual review is recommended."
    )


def verify_education(
    db: Session,
    applicant_id: uuid.UUID,
    requested_by_id: uuid.UUID,
    full_name: str,
    school_name: str,
    degree: str,
    graduation_year: int,
    candidate_consent: bool,
) -> EducationVerifyResponse:
    response_data: dict | None = None

    local_match = _lookup_local(db, full_name, school_name, degree, graduation_year)
    if local_match:
        result = EducationVerifyResponse(
            status=VerificationStatus.VERIFIED,
            verified_by=VerificationSource.LOCAL_DB,
            details=VerificationDetails(
                school=local_match.school_name, degree=local_match.degree, year=local_match.graduation_year
            ),
        )
    elif not settings.GHANA_EDU_API_KEY:
        # No external provider configured — can't confirm or deny, so this is
        # "pending" rather than "not_found" (which would wrongly imply we checked).
        result = EducationVerifyResponse(status=VerificationStatus.PENDING, verified_by=None, details=None)
    else:
        result, response_data = _lookup_external(full_name, school_name, degree, graduation_year)

    result = result.model_copy(
        update={"summary": _build_summary(full_name, school_name, degree, graduation_year, result)}
    )

    db.add(
        VerificationLog(
            applicant_id=applicant_id,
            requested_by_id=requested_by_id,
            full_name=full_name,
            school_name=school_name,
            degree=degree,
            graduation_year=graduation_year,
            candidate_consent=candidate_consent,
            status=result.status,
            verified_by=result.verified_by,
            response_data=response_data,
        )
    )
    db.commit()

    return result


def _compare_claim_to_evidence(
    full_name: str,
    school_name: str,
    degree: str,
    graduation_year: int,
    extraction: EducationEvidenceExtraction,
) -> tuple[EducationVerifyResponse, bool]:
    """The only place a VERIFIED/NOT_FOUND/PENDING call gets made for
    evidence-based verification. `extraction` holds only literal facts an LLM
    pulled from the document (see education_evidence_extraction.py) — the
    decision here is plain code, not a model judgment call.

    A claim verifies only if school, degree, and graduation year all match
    what was found in the evidence. If the evidence didn't state enough
    fields to compare, status is PENDING (not enough information yet, same
    meaning PENDING already carries when no external provider is
    configured) rather than a false NOT_FOUND.

    Returns (result, name_flagged). name_flagged is surfaced in the summary
    but never changes the status by itself — a differently-spelled name is a
    caveat for a human reviewer, not grounds to auto-fail an otherwise real
    match.
    """
    fields_present = sum(
        v is not None for v in (extraction.school_name, extraction.degree, extraction.graduation_year)
    )
    name_flagged = (
        extraction.candidate_name is not None
        and _normalize(extraction.candidate_name) != _normalize(full_name)
    )

    if fields_present == 0:
        return EducationVerifyResponse(status=VerificationStatus.PENDING, verified_by=None, details=None), name_flagged

    school_match = extraction.school_name is not None and _normalize(extraction.school_name) == _normalize(school_name)
    degree_match = extraction.degree is not None and _normalize(extraction.degree) == _normalize(degree)
    year_match = extraction.graduation_year is not None and extraction.graduation_year == graduation_year

    if school_match and degree_match and year_match:
        result = EducationVerifyResponse(
            status=VerificationStatus.VERIFIED,
            verified_by=VerificationSource.DOCUMENT_EVIDENCE,
            details=VerificationDetails(
                school=extraction.school_name, degree=extraction.degree, year=extraction.graduation_year
            ),
        )
        return result, name_flagged

    if fields_present < 3:
        # Evidence spoke to some but not all of the claimed fields — too
        # partial to call it a mismatch.
        return EducationVerifyResponse(status=VerificationStatus.PENDING, verified_by=None, details=None), name_flagged

    return (
        EducationVerifyResponse(status=VerificationStatus.NOT_FOUND, verified_by=VerificationSource.DOCUMENT_EVIDENCE, details=None),
        name_flagged,
    )


def _build_evidence_summary(
    full_name: str,
    school_name: str,
    degree: str,
    graduation_year: int,
    result: EducationVerifyResponse,
    name_flagged: bool,
) -> str:
    """Deterministic, template-based HR-facing sentence — NOT an LLM call.
    Mirrors _build_summary's guarantee: it restates only fields already on
    result/the claim, so it can never assert a detail extraction didn't
    actually establish."""
    if result.status == VerificationStatus.VERIFIED and result.details:
        summary = (
            f"The provided evidence document confirms that {full_name} attended "
            f"{result.details.school} and was awarded {result.details.degree} in {result.details.year}."
        )
    elif result.status == VerificationStatus.NOT_FOUND:
        summary = (
            f"The provided evidence document does not confirm that {full_name} attended {school_name} "
            f"or was awarded {degree} in {graduation_year}. Details extracted from the document do not "
            "match the claim."
        )
    else:
        summary = (
            f"The provided evidence document did not contain enough information to confirm or deny that "
            f"{full_name} attended {school_name} for a {degree} ({graduation_year}). Manual review or "
            "additional documentation is recommended."
        )
    if name_flagged:
        summary += (
            " Note: the name on the evidence document does not exactly match the candidate's stated name — "
            "this was not used to auto-verify or auto-reject and should be checked manually."
        )
    return summary


def verify_education_from_evidence(
    db: Session,
    applicant_id: uuid.UUID,
    requested_by_id: uuid.UUID,
    full_name: str,
    school_name: str,
    degree: str,
    graduation_year: int,
    candidate_consent: bool,
    evidence_text: str,
) -> EducationVerifyResponse:
    """Same audit-logged shape as verify_education(), but the source of truth
    is an uploaded/pasted evidence document instead of the local DB or Ghana
    API. extract_education_evidence() may raise
    EvidenceExtractionNotConfiguredError / EvidenceExtractionProviderError /
    EvidenceExtractionError — deliberately left uncaught here so the API
    layer can translate them (503/502/422), matching the rewrite-suggestions
    endpoint's pattern.
    """
    extraction = extract_education_evidence(evidence_text)

    result, name_flagged = _compare_claim_to_evidence(full_name, school_name, degree, graduation_year, extraction)
    result = result.model_copy(
        update={
            "summary": _build_evidence_summary(full_name, school_name, degree, graduation_year, result, name_flagged)
        }
    )

    db.add(
        VerificationLog(
            applicant_id=applicant_id,
            requested_by_id=requested_by_id,
            full_name=full_name,
            school_name=school_name,
            degree=degree,
            graduation_year=graduation_year,
            candidate_consent=candidate_consent,
            status=result.status,
            verified_by=result.verified_by,
            response_data=extraction.model_dump(),
        )
    )
    db.commit()

    return result
