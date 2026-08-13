"""Skill exaggeration detection: flags claimed skills that have no
supporting evidence anywhere in the experience/projects text.
"""
import re

from app.schemas.analysis import FraudFlag
from app.schemas.resume import ParsedResume
from app.services.fraud.common import clamp, make_flag

# Skills that are hard to fake in passing (rarely name-dropped without use)
# vs. skills that are commonly listed superficially.
HIGH_SIGNAL_SKILLS = {
    "kubernetes", "tensorflow", "pytorch", "rust", "go", "terraform", "graphql",
    "machine learning", "deep learning", "microservices", "aws", "azure", "gcp",
}


def analyze_skills(parsed: ParsedResume) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    penalty = 0.0

    if not parsed.skills:
        return 0.0, flags

    evidence_text = " ".join(
        [e.raw_text for e in parsed.experience] + parsed.projects + parsed.certifications
    ).lower()

    unsupported: list[str] = []
    for skill in parsed.skills:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        if not re.search(pattern, evidence_text):
            unsupported.append(skill)

    total = len(parsed.skills)
    unsupported_ratio = len(unsupported) / total if total else 0

    if total >= 8 and unsupported_ratio >= 0.6:
        penalty += 35
        flags.append(
            make_flag(
                "skills",
                "high",
                "Possible skill exaggeration",
                f"{len(unsupported)} of {total} claimed skills ({unsupported_ratio:.0%}) have no "
                "supporting mention in the experience, projects, or certifications sections.",
                unsupported[:10],
            )
        )
    elif total >= 5 and unsupported_ratio >= 0.4:
        penalty += 18
        flags.append(
            make_flag(
                "skills",
                "medium",
                "Some claimed skills lack supporting evidence",
                f"{len(unsupported)} of {total} claimed skills aren't referenced elsewhere in the resume.",
                unsupported[:10],
            )
        )

    unsupported_high_signal = [s for s in unsupported if s in HIGH_SIGNAL_SKILLS]
    if len(unsupported_high_signal) >= 3:
        penalty += 20
        flags.append(
            make_flag(
                "skills",
                "high",
                "Advanced/specialist skills without evidence",
                "Several specialist technologies are listed but never appear in any project or "
                "role description: " + ", ".join(unsupported_high_signal) + ".",
                unsupported_high_signal,
            )
        )

    if total > 25:
        penalty += 10
        flags.append(
            make_flag(
                "skills",
                "low",
                "Unusually large skill list",
                f"{total} distinct skills were claimed, which is atypical and may indicate "
                "keyword-stuffing rather than genuine proficiency.",
            )
        )

    return clamp(penalty), flags
