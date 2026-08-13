"""Heuristic AI-generated-text detector. Fully local — no external API
calls. Combines several weak signals often associated with LLM-written
resume bullets: buzzword density, uniform sentence length, repeated
sentence openers, and n-gram repetition across bullet points.

This is intentionally a heuristic screening signal, not a definitive
classifier — it is surfaced to recruiters as "possible AI-generated
writing patterns", never as a hard rejection.
"""
import statistics
from collections import Counter

from app.schemas.analysis import FraudFlag
from app.services.fraud.common import clamp, make_flag
from app.services.text_signals import BUZZWORDS, WORD_RE, split_sentences


def analyze_ai_generated(raw_text: str) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    if not raw_text or len(raw_text) < 200:
        return 0.0, flags

    lower = raw_text.lower()
    penalty = 0.0

    # --- Buzzword density ---
    buzz_hits = [b for b in BUZZWORDS if b in lower]
    words = WORD_RE.findall(raw_text)
    word_count = max(len(words), 1)
    buzz_density = len(buzz_hits) / (word_count / 100)  # buzzwords per 100 words

    if buzz_density >= 1.5 and len(buzz_hits) >= 4:
        penalty += 30
        flags.append(
            make_flag(
                "ai_generated",
                "medium",
                "High density of generic/AI-style phrasing",
                "The text is dense with generic corporate buzzwords commonly overused by AI "
                "writing assistants: " + ", ".join(buzz_hits[:8]) + ".",
                buzz_hits[:8],
            )
        )

    # --- Sentence length uniformity ---
    sentences = split_sentences(raw_text)
    if len(sentences) >= 8:
        lengths = [len(s.split()) for s in sentences]
        mean_len = statistics.mean(lengths)
        stdev_len = statistics.pstdev(lengths)
        coefficient_of_variation = (stdev_len / mean_len) if mean_len else 0
        if coefficient_of_variation < 0.28 and mean_len > 8:
            penalty += 20
            flags.append(
                make_flag(
                    "ai_generated",
                    "low",
                    "Unusually uniform sentence structure",
                    "Sentence lengths are highly consistent throughout the document "
                    f"(avg {mean_len:.0f} words, low variance), a pattern more common in "
                    "AI-generated text than natural writing.",
                )
            )

    # --- Repeated sentence openers ---
    openers = [s.split()[0].lower() for s in sentences if s.split()]
    opener_counts = Counter(openers)
    dominant_opener, dominant_count = (opener_counts.most_common(1) or [(None, 0)])[0]
    if sentences and dominant_count >= max(4, int(len(sentences) * 0.35)):
        penalty += 15
        flags.append(
            make_flag(
                "ai_generated",
                "low",
                "Repetitive sentence openers",
                f"{dominant_count} of {len(sentences)} sentences/bullets start with the same "
                f"word (\"{dominant_opener}\"), suggesting templated or auto-generated phrasing.",
            )
        )

    # --- Repeated trigram structures across bullets (template reuse) ---
    trigrams = []
    for s in sentences:
        tokens = [w.lower() for w in WORD_RE.findall(s)]
        trigrams.extend(" ".join(tokens[i : i + 3]) for i in range(max(len(tokens) - 2, 0)))
    trigram_counts = Counter(trigrams)
    repeated_trigrams = [t for t, c in trigram_counts.items() if c >= 3 and len(t) > 10]
    if repeated_trigrams:
        penalty += 15
        flags.append(
            make_flag(
                "ai_generated",
                "low",
                "Repeated phrase templates",
                "The same short phrase structure recurs across multiple bullet points: \""
                + repeated_trigrams[0] + "\".",
                repeated_trigrams[:5],
            )
        )

    return clamp(penalty), flags
