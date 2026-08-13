"""Duplicate resume detection: exact-text fingerprint matching plus
semantic similarity (Sentence-Transformer embeddings + cosine similarity)
against previously submitted resumes.
"""
import hashlib

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.schemas.analysis import FraudFlag
from app.services.fraud.common import clamp, make_flag
from app.services.nlp import get_sentence_transformer

SEMANTIC_CANDIDATE_LIMIT = 300
HIGH_SIMILARITY_THRESHOLD = 0.92
MEDIUM_SIMILARITY_THRESHOLD = 0.80


def compute_fingerprint(raw_text: str) -> str:
    normalized = " ".join(raw_text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_duplicates(db: Session, current_resume_id, raw_text: str, fingerprint: str) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    penalty = 0.0

    if not raw_text or not raw_text.strip():
        return 0.0, flags

    exact_matches = db.scalars(
        select(Resume).where(Resume.text_fingerprint == fingerprint, Resume.id != current_resume_id)
    ).all()
    if exact_matches:
        penalty += 60
        flags.append(
            make_flag(
                "duplicate",
                "high",
                "Exact duplicate resume text",
                f"This resume's text is byte-for-byte identical (after whitespace normalization) "
                f"to {len(exact_matches)} previously submitted resume(s).",
                [str(m.id) for m in exact_matches[:5]],
            )
        )
        return clamp(penalty), flags

    candidates = db.scalars(
        select(Resume)
        .where(Resume.id != current_resume_id, Resume.raw_text.is_not(None))
        .order_by(Resume.created_at.desc())
        .limit(SEMANTIC_CANDIDATE_LIMIT)
    ).all()
    candidates = [c for c in candidates if c.raw_text and c.raw_text.strip()]
    if not candidates:
        return 0.0, flags

    model = get_sentence_transformer()
    corpus_texts = [c.raw_text for c in candidates]
    embeddings = model.encode([raw_text] + corpus_texts, normalize_embeddings=True)
    query_vec = embeddings[0]
    corpus_vecs = embeddings[1:]

    similarities = corpus_vecs @ query_vec  # cosine similarity, vectors are normalized
    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])

    if best_score >= HIGH_SIMILARITY_THRESHOLD:
        penalty += 55
        flags.append(
            make_flag(
                "duplicate",
                "high",
                "Likely duplicate submission",
                f"This resume is {best_score:.0%} semantically similar to a previously submitted "
                f"resume (id {candidates[best_idx].id}).",
                [str(candidates[best_idx].id)],
            )
        )
    elif best_score >= MEDIUM_SIMILARITY_THRESHOLD:
        penalty += 25
        flags.append(
            make_flag(
                "duplicate",
                "medium",
                "Similar to a previous submission",
                f"This resume is {best_score:.0%} semantically similar to a previously submitted "
                f"resume (id {candidates[best_idx].id}). Could be a template reuse or resubmission.",
                [str(candidates[best_idx].id)],
            )
        )

    return clamp(penalty), flags
