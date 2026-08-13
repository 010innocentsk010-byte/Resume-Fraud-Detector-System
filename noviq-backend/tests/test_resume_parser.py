from app.services.resume_parser import extract_bullet_lines, extract_skills, parse_resume_text, split_into_sections

SAMPLE_RESUME = """
John Doe
john.doe@example.com
+1 555-123-4567

Summary
Experienced software engineer.

Experience
Senior Software Engineer at Acme Corp
Jan 2020 - Present
Built scalable backend services using Python and Kubernetes.

Software Engineer at Beta Inc
Jun 2017 - Dec 2019
Developed REST APIs.

Education
Bachelor of Science in Computer Science
2013 - 2017

Skills
Python, Docker, Kubernetes, AWS, SQL

Certifications
AWS Certified Solutions Architect

Projects
Personal portfolio website
"""


def test_extracts_contact_info():
    parsed = parse_resume_text(SAMPLE_RESUME)
    assert parsed.contact.email == "john.doe@example.com"
    assert parsed.contact.phone is not None


def test_extracts_skills():
    parsed = parse_resume_text(SAMPLE_RESUME)
    assert "python" in parsed.skills
    assert "kubernetes" in parsed.skills
    assert "aws" in parsed.skills


def test_extracts_education_with_years():
    parsed = parse_resume_text(SAMPLE_RESUME)
    assert len(parsed.education) >= 1
    edu = parsed.education[0]
    assert edu.start_year == 2013
    assert edu.end_year == 2017


def test_extracts_experience_entries():
    parsed = parse_resume_text(SAMPLE_RESUME)
    assert len(parsed.experience) == 2
    current_roles = [e for e in parsed.experience if e.is_current]
    assert len(current_roles) == 1


def test_detects_sections():
    parsed = parse_resume_text(SAMPLE_RESUME)
    assert "experience" in parsed.sections_found
    assert "education" in parsed.sections_found
    assert "skills" in parsed.sections_found


def test_handles_empty_text():
    parsed = parse_resume_text("")
    assert parsed.skills == []
    assert parsed.education == []
    assert parsed.experience == []


def test_split_into_sections():
    sections = split_into_sections(SAMPLE_RESUME)
    assert "experience" in sections
    assert "Senior Software Engineer at Acme Corp" in sections["experience"]


def test_extract_skills_public_helper():
    assert extract_skills("I have used Python and Kubernetes extensively.") == ["kubernetes", "python"]


def test_extract_bullet_lines():
    lines = extract_bullet_lines(SAMPLE_RESUME)
    assert any("Built scalable backend services" in line for line in lines)
    # Short lines (fewer than 4 words, e.g. bare date ranges or "Developed REST APIs.")
    # are intentionally filtered out — they're headings/fragments, not rewrite-worthy bullets.
    assert all(len(line.split()) >= 4 for line in lines)
