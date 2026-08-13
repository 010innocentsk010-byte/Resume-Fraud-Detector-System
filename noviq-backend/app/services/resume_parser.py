"""Heuristic resume structuring: turns raw extracted text into a
ParsedResume (contact info, skills, education, experience, certifications,
projects). Fully local — regex + section-header detection + spaCy NER,
no external API calls.
"""
import re
from dataclasses import dataclass, field

from app.schemas.resume import ParsedContact, ParsedEducationEntry, ParsedExperienceEntry, ParsedResume
from app.services.nlp import get_spacy_model

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}")
YEAR_RE = re.compile(r"(19|20)\d{2}")
DATE_RANGE_RE = re.compile(
    r"(?P<start>(?:[A-Za-z]{3,9}\.?\s+)?(?:19|20)\d{2})\s*(?:-|–|—|to)\s*"
    r"(?P<end>(?:[A-Za-z]{3,9}\.?\s+)?(?:19|20)\d{2}|present|current|now)",
    re.IGNORECASE,
)

SECTION_ALIASES: dict[str, list[str]] = {
    "experience": ["experience", "work experience", "employment history", "professional experience", "work history"],
    "education": ["education", "academic background", "academic qualifications"],
    "skills": ["skills", "technical skills", "core competencies", "key skills"],
    "certifications": ["certifications", "certificates", "licenses", "certifications & licenses"],
    "projects": ["projects", "personal projects", "key projects"],
    "summary": ["summary", "profile", "objective", "professional summary"],
}

COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin",
    "sql", "nosql", "postgresql", "mysql", "mongodb", "redis",
    "react", "next.js", "vue", "angular", "node.js", "express", "django", "flask", "fastapi", "spring",
    "docker", "kubernetes", "terraform", "ansible", "jenkins", "ci/cd",
    "aws", "azure", "gcp", "google cloud",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "nlp", "computer vision",
    "html", "css", "tailwind", "sass",
    "git", "linux", "bash", "graphql", "rest api", "microservices",
    "excel", "tableau", "power bi", "data analysis", "project management", "agile", "scrum",
]

DEGREE_RE = re.compile(
    r"\b(bachelor(?:'s)?|b\.?sc|b\.?a|b\.?eng|b\.?tech|master(?:'s)?|m\.?sc|m\.?a|m\.?eng|m\.?tech|mba|ph\.?d|"
    r"doctorate|associate(?:'s)?|diploma|hnd)\b",
    re.IGNORECASE,
)


@dataclass
class _SectionSplit:
    sections: dict[str, str] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)


def _split_sections(text: str) -> _SectionSplit:
    lines = text.splitlines()
    result = _SectionSplit()
    current_key = "header"
    buffer: list[str] = []

    def flush():
        if buffer:
            result.sections[current_key] = result.sections.get(current_key, "") + "\n".join(buffer) + "\n"

    for line in lines:
        stripped = line.strip().lower().strip(":").strip()
        matched_key = None
        if 0 < len(stripped) <= 40:
            for key, aliases in SECTION_ALIASES.items():
                if stripped in aliases:
                    matched_key = key
                    break
        if matched_key:
            flush()
            buffer = []
            current_key = matched_key
            if matched_key not in result.order:
                result.order.append(matched_key)
        else:
            buffer.append(line)
    flush()
    return result


def _extract_contact(text: str) -> ParsedContact:
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    name = None
    try:
        nlp = get_spacy_model()
        head = "\n".join(text.splitlines()[:10])
        doc = nlp(head)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                break
    except Exception:
        name = None

    return ParsedContact(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0).strip() if phone_match else None,
    )


def extract_skills(text: str) -> list[str]:
    """Match COMMON_SKILLS against a plain text blob. Public entry point reused
    by job_match.py to score JD skill overlap against a resume's parsed skills."""
    haystack = text.lower()
    found = []
    for skill in COMMON_SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, haystack):
            found.append(skill)
    return sorted(set(found))


def _extract_skills(sections: _SectionSplit, full_text: str) -> list[str]:
    return extract_skills(sections.sections.get("skills", "") + "\n" + full_text)


def split_into_sections(text: str) -> dict[str, str]:
    """Public wrapper around the section-header splitter, reused by the
    per-section AI detector and the AI-rewrite bullet extractor."""
    return _split_sections(text).sections


def extract_bullet_lines(text: str, keys: tuple[str, ...] = ("experience", "projects")) -> list[str]:
    """Pull individual bullet/line-level statements out of the given resume
    sections (bullet markers stripped, short heading/date-only lines dropped).
    Used by rewrite_suggestions.py to find candidate lines to rewrite."""
    sections = split_into_sections(text)
    lines: list[str] = []
    for key in keys:
        block = sections.get(key, "")
        for raw_line in block.splitlines():
            line = raw_line.strip(" \t-•*").strip()
            if line and len(line.split()) >= 4:
                lines.append(line)
    return lines


def _extract_education(sections: _SectionSplit) -> list[ParsedEducationEntry]:
    block = sections.sections.get("education", "")
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    entries: list[ParsedEducationEntry] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        degree_match = DEGREE_RE.search(line)
        years = [int(m.group(0)) for m in YEAR_RE.finditer(line)]

        if not degree_match and not years:
            i += 1
            continue

        raw_text = line
        # Degree and dates are often on separate lines (degree name, then a
        # "2016 - 2020" line right below it) — merge that pair into one entry.
        if degree_match and not years and i + 1 < len(lines):
            next_years = [int(m.group(0)) for m in YEAR_RE.finditer(lines[i + 1])]
            if next_years and not DEGREE_RE.search(lines[i + 1]):
                years = next_years
                raw_text = f"{line} ({lines[i + 1]})"
                i += 1

        entries.append(
            ParsedEducationEntry(
                degree=degree_match.group(0) if degree_match else None,
                field=None,
                institution=None,
                start_year=min(years) if years else None,
                end_year=max(years) if years else None,
                raw_text=raw_text,
            )
        )
        i += 1
    return entries


TITLE_COMPANY_RE = re.compile(r"^(?P<title>.+?)\s+(?:at|[-–—@])\s+(?P<company>.+)$")


def _extract_experience(sections: _SectionSplit) -> list[ParsedExperienceEntry]:
    block = sections.sections.get("experience", "")
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    entries: list[ParsedExperienceEntry] = []

    for idx, raw_line in enumerate(lines):
        date_match = DATE_RANGE_RE.search(raw_line)
        if not date_match:
            continue

        end_raw = date_match.group("end").strip().lower()
        is_current = end_raw in ("present", "current", "now")

        title, company = None, None
        raw_text = raw_line
        # The role title and employer are conventionally on the line right before
        # the date range, e.g. "Senior Engineer at Acme Corp" / "Jan 2020 - Present".
        if idx > 0 and not DATE_RANGE_RE.search(lines[idx - 1]):
            heading = lines[idx - 1]
            heading_match = TITLE_COMPANY_RE.match(heading)
            if heading_match:
                title = heading_match.group("title").strip()
                company = heading_match.group("company").strip()
            else:
                title = heading
            raw_text = f"{heading} ({raw_line})"

        entries.append(
            ParsedExperienceEntry(
                title=title,
                company=company,
                start_date=date_match.group("start").strip(),
                end_date="present" if is_current else date_match.group("end").strip(),
                is_current=is_current,
                raw_text=raw_text,
            )
        )
    return entries


def _extract_list_section(sections: _SectionSplit, key: str) -> list[str]:
    block = sections.sections.get(key, "")
    items = []
    for raw_line in block.splitlines():
        line = raw_line.strip(" \t-•*").strip()
        if line:
            items.append(line)
    return items


def parse_resume_text(text: str) -> ParsedResume:
    sections = _split_sections(text)
    return ParsedResume(
        contact=_extract_contact(text),
        skills=_extract_skills(sections, text),
        education=_extract_education(sections),
        experience=_extract_experience(sections),
        certifications=_extract_list_section(sections, "certifications"),
        projects=_extract_list_section(sections, "projects"),
        sections_found=sections.order,
    )
