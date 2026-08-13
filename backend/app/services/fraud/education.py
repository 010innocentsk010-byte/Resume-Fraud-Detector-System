"""Education consistency analysis: impossible timelines and overlapping
full-time degree programs.
"""
from app.schemas.analysis import FraudFlag
from app.schemas.resume import ParsedResume
from app.services.fraud.common import clamp, make_flag

# Minimum realistic duration (years) for a full-time program of this level.
MIN_PROGRAM_YEARS = {
    "bachelor": 3,
    "b.sc": 3,
    "bsc": 3,
    "b.a": 3,
    "ba": 3,
    "b.eng": 3,
    "beng": 3,
    "b.tech": 3,
    "btech": 3,
    "master": 1,
    "m.sc": 1,
    "msc": 1,
    "m.a": 1,
    "ma": 1,
    "mba": 1,
    "m.eng": 1,
    "meng": 1,
    "m.tech": 1,
    "mtech": 1,
    "ph.d": 3,
    "phd": 3,
    "doctorate": 3,
    "associate": 1,
    "diploma": 1,
    "hnd": 1,
}


def _normalized_degree(degree: str | None) -> str | None:
    if not degree:
        return None
    return degree.lower().replace("'s", "").strip()


def analyze_education(parsed: ParsedResume) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    penalty = 0.0

    if not parsed.education:
        return 0.0, flags

    dated = [e for e in parsed.education if e.start_year and e.end_year]

    for edu in dated:
        duration = edu.end_year - edu.start_year
        if duration < 0:
            penalty += 25
            flags.append(
                make_flag(
                    "education",
                    "high",
                    "Invalid education date range",
                    f"End year precedes start year: \"{edu.raw_text}\".",
                    [edu.raw_text],
                )
            )
            continue

        norm = _normalized_degree(edu.degree)
        min_years = MIN_PROGRAM_YEARS.get(norm, 0) if norm else 0
        if duration < min_years and duration <= 1 and min_years >= 3:
            penalty += 20
            flags.append(
                make_flag(
                    "education",
                    "high",
                    "Unrealistic program duration",
                    f"\"{edu.raw_text}\" spans only {duration} year(s), shorter than a typical "
                    f"full-time program of this type (~{min_years}+ years).",
                    [edu.raw_text],
                )
            )

    dated_sorted = sorted(dated, key=lambda e: e.start_year)
    for i in range(len(dated_sorted) - 1):
        cur, nxt = dated_sorted[i], dated_sorted[i + 1]
        gap = nxt.start_year - cur.end_year
        if gap < 0 and min(cur.end_year, nxt.end_year) - max(cur.start_year, nxt.start_year) >= 1:
            penalty += 15
            flags.append(
                make_flag(
                    "education",
                    "medium",
                    "Overlapping full-time degree programs",
                    f"\"{cur.raw_text}\" and \"{nxt.raw_text}\" overlap by a year or more.",
                    [cur.raw_text, nxt.raw_text],
                )
            )
    undated = [e for e in parsed.education if not (e.start_year and e.end_year)]
    if undated and len(parsed.education) == len(undated):
        penalty += 5
        flags.append(
            make_flag(
                "education",
                "low",
                "Education dates missing",
                "No verifiable start/end years were found for the listed education entries.",
            )
        )

    return clamp(penalty), flags
