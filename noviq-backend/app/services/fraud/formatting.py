"""Suspicious formatting detection: hidden/invisible characters (a known
ATS keyword-stuffing trick), missing section structure, and other
formatting anomalies extracted text can reveal.
"""
import re
import unicodedata

from app.schemas.analysis import FraudFlag
from app.schemas.resume import ParsedResume
from app.services.fraud.common import clamp, make_flag

ZERO_WIDTH_CHARS = [
    "​",  # zero-width space
    "‌",  # zero-width non-joiner
    "‍",  # zero-width joiner
    "﻿",  # byte-order mark / zero-width no-break space
    "⁠",  # word joiner
]


def analyze_formatting(raw_text: str, parsed: ParsedResume) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    penalty = 0.0

    if not raw_text:
        return 0.0, flags

    hidden_count = sum(raw_text.count(ch) for ch in ZERO_WIDTH_CHARS)
    if hidden_count > 0:
        penalty += 40
        flags.append(
            make_flag(
                "formatting",
                "high",
                "Hidden/invisible characters detected",
                f"{hidden_count} zero-width or invisible unicode character(s) were found in the "
                "document text — often used to hide extra keywords from human readers while "
                "still being picked up by ATS parsers.",
            )
        )

    control_chars = sum(
        1 for ch in raw_text if unicodedata.category(ch) == "Cc" and ch not in ("\n", "\t", "\r")
    )
    if control_chars > 5:
        penalty += 15
        flags.append(
            make_flag(
                "formatting",
                "medium",
                "Unusual control characters",
                f"{control_chars} non-standard control characters were found in the extracted text.",
            )
        )

    if len(parsed.sections_found) < 2:
        penalty += 15
        flags.append(
            make_flag(
                "formatting",
                "medium",
                "No clear resume structure detected",
                "Standard section headers (Experience, Education, Skills, ...) could not be "
                "identified, which may indicate an unusual template designed to confuse ATS/parsers, "
                "or a scanned/image-based document with poor text extraction.",
            )
        )

    long_lines = [line for line in raw_text.splitlines() if len(line) > 500]
    if long_lines:
        penalty += 10
        flags.append(
            make_flag(
                "formatting",
                "low",
                "Abnormally long text lines",
                f"{len(long_lines)} line(s) exceed 500 characters, suggesting missing structure "
                "or table/column content that didn't extract cleanly.",
            )
        )

    whitespace_runs = re.findall(r"[ \t]{15,}", raw_text)
    if len(whitespace_runs) > 3:
        penalty += 8
        flags.append(
            make_flag(
                "formatting",
                "low",
                "Excessive whitespace padding",
                "Multiple large runs of whitespace were found, sometimes used to bury repeated "
                "keywords off-screen.",
            )
        )

    return clamp(penalty), flags
