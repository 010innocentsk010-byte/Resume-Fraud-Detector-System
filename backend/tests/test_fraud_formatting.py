from app.schemas.resume import ParsedResume
from app.services.fraud.formatting import analyze_formatting


def _parsed(sections_found=None) -> ParsedResume:
    return ParsedResume(contact={}, skills=[], education=[], experience=[], sections_found=sections_found or [])


def test_empty_text_no_flags():
    score, flags = analyze_formatting("", _parsed())
    assert score == 0
    assert flags == []


def test_hidden_characters_flagged():
    zwsp = "​"
    text = f"Experienced engineer.{zwsp}Python{zwsp}Java{zwsp}" * 3
    score, flags = analyze_formatting(text, _parsed(["experience"]))
    assert score > 0
    assert any(f.title == "Hidden/invisible characters detected" for f in flags)


def test_missing_structure_flagged():
    text = "Just some plain unstructured text with no headers at all describing a candidate."
    score, flags = analyze_formatting(text, _parsed(sections_found=[]))
    assert any(f.title == "No clear resume structure detected" for f in flags)


def test_well_structured_resume_not_flagged_for_structure():
    text = "Some resume text with clear sections."
    score, flags = analyze_formatting(text, _parsed(sections_found=["experience", "education", "skills"]))
    assert not any(f.title == "No clear resume structure detected" for f in flags)
