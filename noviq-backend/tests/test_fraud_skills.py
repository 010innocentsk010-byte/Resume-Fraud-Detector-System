from app.schemas.resume import ParsedExperienceEntry, ParsedResume
from app.services.fraud.skills import analyze_skills


def _resume(skills, experience=None, projects=None) -> ParsedResume:
    return ParsedResume(
        contact={},
        skills=skills,
        education=[],
        experience=experience or [],
        projects=projects or [],
        sections_found=[],
    )


def test_no_skills_no_flags():
    score, flags = analyze_skills(_resume([]))
    assert score == 0
    assert flags == []


def test_unsupported_skills_flagged():
    skills = ["python", "java", "go", "rust", "kubernetes", "tensorflow", "docker", "aws"]
    exp = ParsedExperienceEntry(raw_text="Built a static website using HTML only.")
    score, flags = analyze_skills(_resume(skills, experience=[exp]))
    assert score > 0
    assert any(f.title == "Possible skill exaggeration" for f in flags)


def test_supported_skills_no_exaggeration_flag():
    skills = ["python", "docker"]
    exp = ParsedExperienceEntry(raw_text="Used Python and Docker to build backend services.")
    score, flags = analyze_skills(_resume(skills, experience=[exp]))
    assert not any(f.title == "Possible skill exaggeration" for f in flags)


def test_large_skill_list_flagged():
    skills = [f"skill{i}" for i in range(30)]
    score, flags = analyze_skills(_resume(skills))
    assert any(f.title == "Unusually large skill list" for f in flags)
