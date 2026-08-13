from app.services.ai_section_detector import analyze_ai_by_section

RESUME_TEXT = """John Smith
john@example.com

Skills
Results-driven, detail-oriented professional leveraging cutting-edge solutions. Proven track record utilizing best-in-class, innovative solutions to streamline workflows and facilitate seamless outcomes.

Experience
I spent the last three years at a mid-sized fintech company where I mostly worked on the payments team. Honestly the biggest win was untangling a gnarly reconciliation job that used to fail every other week — took me about a month of digging through logs.
"""


def test_empty_text_returns_no_sections():
    assert analyze_ai_by_section("") == []


def test_short_sections_excluded():
    scores = analyze_ai_by_section("Skills\nPython.\n")
    assert scores == []


def test_buzzword_section_scores_higher_than_natural_section():
    scores = {s.section: s.ai_confidence for s in analyze_ai_by_section(RESUME_TEXT)}
    assert "skills" in scores
    assert "experience" in scores
    assert scores["skills"] > scores["experience"]


def test_buzzword_section_has_signals():
    scores = {s.section: s.signals for s in analyze_ai_by_section(RESUME_TEXT)}
    assert scores["skills"]
