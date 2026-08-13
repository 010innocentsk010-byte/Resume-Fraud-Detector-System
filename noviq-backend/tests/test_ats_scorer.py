from app.schemas.resume import ParsedContact, ParsedResume
from app.services.ats_scorer import analyze_ats_score

GOOD_TEXT = "\n".join(["This is a well formed resume sentence with real content."] * 40)


def _parsed(email="jane@example.com", phone="555-123-4567", skills=None, sections_found=None) -> ParsedResume:
    return ParsedResume(
        contact=ParsedContact(name="Jane Doe", email=email, phone=phone),
        skills=skills if skills is not None else ["python", "sql"],
        education=[],
        experience=[],
        sections_found=sections_found if sections_found is not None else ["experience", "education", "skills"],
    )


def test_empty_text_scores_zero():
    score, flags = analyze_ats_score("", _parsed())
    assert score == 0.0
    assert any(f.title == "No extractable text" for f in flags)


def test_missing_email_penalized():
    score, flags = analyze_ats_score(GOOD_TEXT, _parsed(email=None))
    assert any(f.title == "Missing contact email" for f in flags)
    assert score < 100


def test_hidden_chars_penalized():
    zwsp = "​"
    text = GOOD_TEXT + zwsp * 3
    score, flags = analyze_ats_score(text, _parsed())
    assert any(f.title == "Hidden characters may break ATS parsing" for f in flags)


def test_few_sections_penalized():
    score, flags = analyze_ats_score(GOOD_TEXT, _parsed(sections_found=["experience"]))
    assert any(f.title == "Few standard section headers detected" for f in flags)


def test_well_formed_resume_scores_high():
    score, flags = analyze_ats_score(GOOD_TEXT, _parsed())
    assert score >= 90
    assert flags == []
