"""Per-section heuristic AI-generated-text detector. Fully local — no
external API calls. Unlike app.services.fraud.ai_text_detection (which
scores the whole document as one blended fraud-risk input), this scores
each resume *section* independently so the UI can surface something like
"This section looks 85% AI written" per section, rather than one buried
whole-document number.

Deliberately narrower than the whole-document detector: repeated-openers
and trigram-repetition checks are noisy on short, single-section text, so
only buzzword density and sentence-length uniformity are used here, with
thresholds tuned down for shorter text.
"""
import statistics

from app.schemas.analysis import SectionAIScore
from app.services.fraud.common import clamp
from app.services.resume_parser import split_into_sections
from app.services.text_signals import BUZZWORDS, WORD_RE, split_sentences

MIN_SECTION_CHARS = 80
SECTION_KEYS = ("summary", "experience", "education", "skills", "certifications", "projects")


def _score_section(text: str) -> tuple[float, list[str]]:
    signals: list[str] = []
    confidence = 0.0

    lower = text.lower()
    words = WORD_RE.findall(text)
    word_count = max(len(words), 1)
    buzz_hits = [b for b in BUZZWORDS if b in lower]
    buzz_density = len(buzz_hits) / (word_count / 100)

    if buzz_density >= 1.5 and len(buzz_hits) >= 2:
        confidence += 45
        signals.append(f"Dense generic/corporate phrasing ({len(buzz_hits)} buzzwords in {word_count} words).")

    sentences = split_sentences(text)
    if len(sentences) >= 2:
        lengths = [len(s.split()) for s in sentences]
        mean_len = statistics.mean(lengths)
        stdev_len = statistics.pstdev(lengths)
        coefficient_of_variation = (stdev_len / mean_len) if mean_len else 0
        if coefficient_of_variation < 0.28 and mean_len > 8:
            confidence += 35
            signals.append(
                f"Unusually uniform sentence length (avg {mean_len:.0f} words, low variance)."
            )

    return clamp(confidence), signals


def analyze_ai_by_section(raw_text: str) -> list[SectionAIScore]:
    if not raw_text:
        return []

    sections = split_into_sections(raw_text)
    scores: list[SectionAIScore] = []
    for key in SECTION_KEYS:
        text = sections.get(key, "").strip()
        if len(text) < MIN_SECTION_CHARS:
            continue
        confidence, signals = _score_section(text)
        scores.append(SectionAIScore(section=key, ai_confidence=confidence, signals=signals))
    return scores
