"""Heuristic ATS (Applicant Tracking System) parseability scorer. Fully
local — no external API calls. This is a "how well will this document
parse" signal, not a fraud signal: it starts at 100 and subtracts points
for things known to trip up ATS parsers (missing contact info, no
section structure, hidden characters, overly dense/short content).
"""
from app.schemas.analysis import FraudFlag
from app.schemas.resume import ParsedResume
from app.services.fraud.common import clamp, make_flag
from app.services.fraud.formatting import ZERO_WIDTH_CHARS

CATEGORY = "ats"


def analyze_ats_score(raw_text: str, parsed: ParsedResume) -> tuple[float, list[FraudFlag]]:
    flags: list[FraudFlag] = []
    penalty = 0.0

    if not raw_text or not raw_text.strip():
        return 0.0, [
            make_flag(CATEGORY, "high", "No extractable text", "No text could be extracted from this document.")
        ]

    if not parsed.contact.email:
        penalty += 25
        flags.append(
            make_flag(
                CATEGORY,
                "high",
                "Missing contact email",
                "No email address was detected. ATS systems and recruiters rely on a clearly "
                "extractable email address to route and contact candidates.",
            )
        )

    if not parsed.contact.phone:
        penalty += 10
        flags.append(
            make_flag(
                CATEGORY,
                "low",
                "Missing contact phone number",
                "No phone number was detected in the document text.",
            )
        )

    if len(parsed.sections_found) < 2:
        penalty += 25
        flags.append(
            make_flag(
                CATEGORY,
                "high",
                "Few standard section headers detected",
                "Standard section headers (Experience, Education, Skills, ...) could not be "
                "reliably identified. ATS parsers rely on these headers to bucket content "
                "correctly — an unusual template or layout can cause fields to be dropped or "
                "misclassified.",
            )
        )

    hidden_count = sum(raw_text.count(ch) for ch in ZERO_WIDTH_CHARS)
    if hidden_count > 0:
        penalty += 20
        flags.append(
            make_flag(
                CATEGORY,
                "high",
                "Hidden characters may break ATS parsing",
                f"{hidden_count} zero-width or invisible unicode character(s) were found, which "
                "can corrupt keyword matching and text extraction in ATS parsers.",
            )
        )

    word_count = len(raw_text.split())
    if word_count < 150:
        penalty += 15
        flags.append(
            make_flag(
                CATEGORY,
                "medium",
                "Resume content is unusually brief",
                f"Only {word_count} words of extractable content were found. Very short "
                "documents often mean an ATS parser is missing content (e.g. text embedded "
                "in an image or unusual layout) rather than a genuinely brief resume.",
            )
        )

    long_lines = [line for line in raw_text.splitlines() if len(line) > 500]
    if long_lines:
        penalty += 15
        flags.append(
            make_flag(
                CATEGORY,
                "medium",
                "Complex layout may not parse cleanly (tables/columns)",
                f"{len(long_lines)} abnormally long line(s) were found in the extracted text, "
                "often a sign of multi-column layouts or tables that ATS parsers read out of "
                "order or merge together.",
            )
        )

    if len(parsed.skills) == 0:
        penalty += 10
        flags.append(
            make_flag(
                CATEGORY,
                "medium",
                "No recognizable skills section found",
                "No recognizable skills were detected. Many ATS systems rank candidates "
                "heavily on keyword/skill matches — an explicit skills section improves match "
                "rates.",
            )
        )

    return clamp(100 - penalty), flags
