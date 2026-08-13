"""Education Evidence Extraction — the only place an LLM touches education
verification. Claude extracts literal fields from unstructured evidence text
(a pasted transcript, certificate-scan OCR, or registrar email); it never
decides VERIFIED/NOT_VERIFIED. That decision stays deterministic, in
education_verification.py's _compare_claim_to_evidence(), so the audit trail
behind a hiring decision never rests on a model's judgment call — only on
plain code comparing extracted facts to the candidate's claim.

Fails closed and cheaply: if ANTHROPIC_API_KEY isn't configured, we raise
before ever constructing a client or making a network call.
"""
import json

import anthropic

from app.core.config import settings
from app.schemas.education_verification import EducationEvidenceExtraction

_SYSTEM_PROMPT = (
    "You extract literal facts from education-verification evidence documents "
    "(transcripts, certificates, registrar emails). You do not verify claims, "
    "decide true or false, or compare anything against a candidate's stated "
    "resume — a separate deterministic process does that. Your only job is "
    "faithful extraction.\n\n"
    "Rules:\n"
    "- Extract a field ONLY if it is explicitly stated in the evidence text. "
    "Never infer, guess, or fill in a plausible-sounding value.\n"
    "- If a field is not present in the evidence, return null for it — do not "
    "omit it or invent a placeholder.\n"
    "- Do not resolve or normalize apparent spelling variants (e.g. a name "
    "spelled differently than expected); extract exactly what the document "
    "says and mention the discrepancy in `notes` instead.\n"
    "- Never use hedging language like 'probably' or 'likely' inside "
    "extracted field values — a field is either the literal text found in "
    "the document, or null.\n"
    "- `notes` is for short, factual observations about the evidence itself "
    "(e.g. 'document is a partial transcript excerpt', 'name spelled "
    "differently than a typical match'). Never use it to render a verdict "
    "on whether the candidate's claim is true."
)

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "school_name": {"type": ["string", "null"]},
        "degree": {"type": ["string", "null"]},
        "graduation_year": {"type": ["integer", "null"]},
        "candidate_name": {"type": ["string", "null"]},
        "notes": {"type": ["string", "null"]},
    },
    "required": ["school_name", "degree", "graduation_year", "candidate_name", "notes"],
    "additionalProperties": False,
}


class EvidenceExtractionError(Exception):
    """Base error for the education-evidence extraction service."""


class EvidenceExtractionNotConfiguredError(EvidenceExtractionError):
    """Missing/invalid ANTHROPIC_API_KEY — surfaced to the API as a 503."""


class EvidenceExtractionProviderError(EvidenceExtractionError):
    """Network/rate-limit/malformed-response failure — surfaced as a 502."""


def extract_education_evidence(evidence_text: str) -> EducationEvidenceExtraction:
    if not evidence_text.strip():
        raise EvidenceExtractionError("Evidence text is empty.")

    if not settings.ANTHROPIC_API_KEY:
        raise EvidenceExtractionNotConfiguredError(
            "Evidence-based education verification requires ANTHROPIC_API_KEY to be configured on the server."
        )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.ANTHROPIC_MAX_OUTPUT_TOKENS,
            system=_SYSTEM_PROMPT,
            thinking={"type": "disabled"},
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA}},
            messages=[{"role": "user", "content": f"Evidence document text:\n\n{evidence_text}"}],
        )
    except anthropic.AuthenticationError as exc:
        raise EvidenceExtractionNotConfiguredError(
            "The configured ANTHROPIC_API_KEY was rejected (invalid key)."
        ) from exc
    except anthropic.PermissionDeniedError as exc:
        raise EvidenceExtractionNotConfiguredError(
            "The configured ANTHROPIC_API_KEY lacks permission for this model."
        ) from exc
    except anthropic.RateLimitError as exc:
        raise EvidenceExtractionProviderError(
            "The evidence extraction service is rate-limited. Please try again shortly."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise EvidenceExtractionProviderError(
            "Could not reach the evidence extraction service. Please try again."
        ) from exc
    except anthropic.APIStatusError as exc:
        raise EvidenceExtractionProviderError(f"Evidence extraction service error: {exc.message}") from exc

    text = next((block.text for block in response.content if block.type == "text"), None)
    if not text:
        raise EvidenceExtractionProviderError("The evidence extraction service returned an empty response.")

    try:
        payload = json.loads(text)
        return EducationEvidenceExtraction(**payload)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EvidenceExtractionProviderError(
            "The evidence extraction service returned a malformed response."
        ) from exc
