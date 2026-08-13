"""Employment timeline analysis: overlapping jobs, invalid date ranges,
and employment that overlaps full-time study periods.
"""
from app.schemas.analysis import FraudFlag
from app.schemas.resume import ParsedResume
from app.services.fraud.common import clamp, extract_year, make_flag


def analyze_timeline(parsed: ParsedResume) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    penalty = 0.0

    intervals: list[tuple[int, int, str]] = []
    for exp in parsed.experience:
        start = extract_year(exp.start_date)
        end = 2100 if exp.is_current else extract_year(exp.end_date)
        if start is None or end is None:
            continue
        if end < start:
            penalty += 25
            flags.append(
                make_flag(
                    "timeline",
                    "high",
                    "Invalid employment date range",
                    f"An entry lists an end date before its start date: \"{exp.raw_text}\".",
                    [exp.raw_text],
                )
            )
            continue
        intervals.append((start, end, exp.raw_text))

    intervals.sort(key=lambda i: i[0])
    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            s1, e1, t1 = intervals[i]
            s2, e2, t2 = intervals[j]
            overlap = min(e1, e2) - max(s1, s2)
            if overlap >= 1:
                penalty += 15
                flags.append(
                    make_flag(
                        "timeline",
                        "medium",
                        "Overlapping employment periods",
                        "Two roles appear to overlap by a year or more, which is unusual for "
                        "full-time positions.",
                        [t1, t2],
                    )
                )

    for edu in parsed.education:
        if edu.start_year is None or edu.end_year is None:
            continue
        for exp_start, exp_end, exp_text in intervals:
            capped_exp_end = min(exp_end, 2100)
            overlap = min(edu.end_year, capped_exp_end) - max(edu.start_year, exp_start)
            if overlap >= 2:
                penalty += 10
                flags.append(
                    make_flag(
                        "timeline",
                        "medium",
                        "Possible timeline inconsistency",
                        f"Employment (\"{exp_text}\") overlaps substantially with full-time study "
                        f"(\"{edu.raw_text}\"). Verify whether the role was part-time.",
                        [exp_text, edu.raw_text],
                    )
                )

    if len(intervals) >= 4:
        bounded_ends = [e for _, e, _ in intervals if e < 2100]
        span = max(bounded_ends) - min(s for s, _, _ in intervals) if bounded_ends else 0
        if span and len(intervals) / max(span, 1) > 1.2:
            penalty += 10
            flags.append(
                make_flag(
                    "timeline",
                    "low",
                    "Rapid job-hopping pattern",
                    f"{len(intervals)} roles reported within roughly {span} year(s), an unusually high turnover rate.",
                )
            )

    return clamp(penalty), flags
