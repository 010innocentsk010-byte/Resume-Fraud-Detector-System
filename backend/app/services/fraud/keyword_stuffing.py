"""Keyword stuffing detection: unnaturally repeated terms, usually meant
to game ATS keyword matching rather than convey real experience.
"""
import re
from collections import Counter

from app.schemas.analysis import FraudFlag
from app.services.fraud.common import clamp, make_flag

STOPWORDS = {
    "the", "and", "for", "with", "a", "an", "of", "to", "in", "on", "at", "as", "is", "are",
    "was", "were", "be", "been", "by", "or", "that", "this", "it", "from", "will", "have",
    "has", "had", "i", "we", "you", "our", "their", "its", "not", "but", "so", "if", "using",
}

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}")


def analyze_keyword_stuffing(raw_text: str) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    if not raw_text or not raw_text.strip():
        return 0.0, flags

    words = [w.lower() for w in WORD_RE.findall(raw_text)]
    meaningful = [w for w in words if w not in STOPWORDS and len(w) > 2]
    total = len(meaningful)
    if total < 20:
        return 0.0, flags

    counts = Counter(meaningful)
    penalty = 0.0
    offenders: list[str] = []

    for term, count in counts.most_common(15):
        ratio = count / total
        if count >= 6 and ratio >= 0.03:
            offenders.append(f"{term} (x{count})")

    consecutive_repeats = re.findall(r"\b(\w{3,})(?:\s*[,;]?\s+\1){2,}\b", raw_text.lower())

    if offenders:
        penalty += min(15 * len(offenders), 60)
        flags.append(
            make_flag(
                "keyword_stuffing",
                "high" if len(offenders) >= 3 else "medium",
                "Keyword stuffing detected",
                "The following terms are repeated far more often than natural writing would "
                "suggest, a common tactic to game ATS keyword matching: " + ", ".join(offenders) + ".",
                offenders,
            )
        )

    if consecutive_repeats:
        penalty += 25
        flags.append(
            make_flag(
                "keyword_stuffing",
                "high",
                "Repeated consecutive keywords",
                "The same word appears multiple times in immediate succession: "
                + ", ".join(sorted(set(consecutive_repeats))[:5]) + ".",
            )
        )

    return clamp(penalty), flags
