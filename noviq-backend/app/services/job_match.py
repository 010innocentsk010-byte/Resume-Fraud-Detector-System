"""Resume <-> Job Description match scoring. Fully local — no external API
calls. Blends a skill-overlap score (against the same COMMON_SKILLS
vocabulary used for resume parsing) with a semantic-similarity score
(Sentence-Transformer embeddings + cosine similarity, the same technique
already used for duplicate-resume detection in
app.services.fraud.duplicate_detection).
"""
from dataclasses import dataclass, field

from app.models.analysis import RiskLevel
from app.models.resume import Resume
from app.services.fraud.common import clamp
from app.services.nlp import get_sentence_transformer
from app.services.resume_parser import extract_skills

SKILL_WEIGHT = 0.6
SEMANTIC_WEIGHT = 0.4

STRONG_MATCH_THRESHOLD = 75
MODERATE_MATCH_THRESHOLD = 45


def build_match_recommendation(match_score: float) -> str:
    if match_score >= STRONG_MATCH_THRESHOLD:
        return "Strong Candidate"
    if match_score >= MODERATE_MATCH_THRESHOLD:
        return "Moderate Candidate"
    return "Weak Candidate"


def is_qualified(match_score: float, risk_level: RiskLevel) -> bool:
    """Auto-qualification rule for the public apply flow: at least a
    Moderate-or-better job match, and fraud risk that isn't High. Both
    signals have to clear — a strong match with High fraud risk still
    doesn't qualify, and vice versa."""
    return match_score >= MODERATE_MATCH_THRESHOLD and risk_level != RiskLevel.HIGH


def compute_skill_overlap(resume_skills: list[str], jd_skills: list[str]) -> tuple[float, list[str], list[str]]:
    """Pure, no I/O. Returns (score 0-100, matched_skills, missing_skills)."""
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    if not jd_set:
        return 0.0, [], []

    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    score = clamp(100 * len(matched) / len(jd_set))
    return score, matched, missing


@dataclass
class JobMatchComputation:
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    semantic_similarity: float
    details: dict = field(default_factory=dict)


def analyze_job_match_batch(resumes: list[Resume], job_description_text: str) -> list[JobMatchComputation]:
    """Match many resumes against one job description, encoding the JD text and
    every resume's text in a single batched embedding call instead of once per
    resume — used by the candidate-ranking endpoint to avoid N redundant
    encodes of the same JD.
    """
    jd_skills = extract_skills(job_description_text)
    jd_text = job_description_text.strip()

    embeddings = None
    if jd_text:
        model = get_sentence_transformer()
        texts = [job_description_text] + [(resume.raw_text or "") for resume in resumes]
        embeddings = model.encode(texts, normalize_embeddings=True)

    results = []
    for i, resume in enumerate(resumes):
        resume_skills = list((resume.parsed_data or {}).get("skills", []))
        skill_score, matched, missing = compute_skill_overlap(resume_skills, jd_skills)

        semantic_similarity = 0.0
        resume_text = resume.raw_text or ""
        if embeddings is not None and resume_text.strip():
            semantic_similarity = float(embeddings[0] @ embeddings[i + 1])

        semantic_score = clamp(semantic_similarity * 100)
        match_score = round(clamp(skill_score * SKILL_WEIGHT + semantic_score * SEMANTIC_WEIGHT), 1)

        results.append(
            JobMatchComputation(
                match_score=match_score,
                matched_skills=matched,
                missing_skills=missing,
                semantic_similarity=round(semantic_similarity, 4),
                details={
                    "skill_score": round(skill_score, 1),
                    "semantic_score": round(semantic_score, 1),
                    "weights": {"skill_score": SKILL_WEIGHT, "semantic_score": SEMANTIC_WEIGHT},
                    "jd_skill_count": len(jd_skills),
                    "resume_skill_count": len(resume_skills),
                },
            )
        )
    return results


def analyze_job_match(resume: Resume, job_description_text: str) -> JobMatchComputation:
    return analyze_job_match_batch([resume], job_description_text)[0]
