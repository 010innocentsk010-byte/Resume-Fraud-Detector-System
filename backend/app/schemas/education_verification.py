import uuid

from pydantic import BaseModel, Field

from app.models.education_verification import VerificationSource, VerificationStatus


class EducationVerifyRequest(BaseModel):
    candidate_id: uuid.UUID = Field(alias="candidateId")
    full_name: str = Field(alias="fullName", min_length=2, max_length=255)
    school_name: str = Field(alias="schoolName", min_length=2, max_length=255)
    degree: str = Field(alias="degree", min_length=2, max_length=255)
    graduation_year: int = Field(alias="graduationYear", ge=1950, le=2100)
    candidate_consent: bool = Field(alias="candidateConsent")

    model_config = {"populate_by_name": True}


class EducationVerifyFromEvidenceRequest(EducationVerifyRequest):
    # Plain text pulled from an uploaded/pasted evidence document (transcript,
    # certificate, registrar email). Whatever produced this text (OCR, paste,
    # email export) happens upstream of this API — the extraction step below
    # only reads it, it doesn't source it.
    evidence_text: str = Field(alias="evidenceText", min_length=1, max_length=20000)


class VerificationDetails(BaseModel):
    school: str
    degree: str
    year: int


class EducationEvidenceExtraction(BaseModel):
    """Literal facts pulled from an evidence document by the extraction
    agent (see app.services.education_evidence_extraction). Every field is
    None unless explicitly stated in the evidence — the extractor never
    infers or guesses, and never renders a VERIFIED/NOT_VERIFIED verdict
    itself. That comparison happens deterministically in
    education_verification.py."""

    school_name: str | None = None
    degree: str | None = None
    graduation_year: int | None = None
    candidate_name: str | None = None
    # Short factual observations only (e.g. a name-spelling discrepancy or a
    # partial document) — never a verdict.
    notes: str | None = None


class EducationVerifyResponse(BaseModel):
    status: VerificationStatus
    verified_by: VerificationSource | None
    details: VerificationDetails | None
    # Deterministic, template-generated HR-facing sentence — not LLM-generated.
    # Built only from fields already on this response, so it can never state
    # anything the verification itself didn't establish. Default "" is an
    # intermediate/unfinalized sentinel; verify_education() always overwrites
    # it before returning to the caller.
    summary: str = ""
