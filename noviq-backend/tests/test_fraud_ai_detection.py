from app.services.fraud.ai_text_detection import analyze_ai_generated

NATURAL_TEXT = """
I spent the last three years at a mid-sized fintech company where I mostly worked on the
payments team. Honestly the biggest win was untangling a gnarly reconciliation job that used
to fail every other week — took me about a month of digging through logs before I found the
root cause. Before that I was at a small agency doing contract work, mostly front-end stuff,
which is where I picked up React. I like debugging more than I like writing new features,
if I'm being honest. Outside of work I maintain a couple of small open-source libraries.
"""

BUZZWORD_TEXT = " ".join(
    [
        "Results-driven, detail-oriented professional leveraging cutting-edge solutions.",
        "Proven track record utilizing best-in-class, innovative solutions to streamline workflows.",
        "Highly motivated self-starter with excellent communication skills and extensive experience.",
        "Passionate about leveraging synergy to facilitate seamless, robust, value-added outcomes.",
    ]
) * 2


def test_short_text_no_flags():
    score, flags = analyze_ai_generated("Short resume.")
    assert score == 0
    assert flags == []


def test_natural_text_low_score():
    score, flags = analyze_ai_generated(NATURAL_TEXT)
    assert score < 30


def test_buzzword_heavy_text_flagged():
    score, flags = analyze_ai_generated(BUZZWORD_TEXT)
    assert score > 0
    assert any(f.title == "High density of generic/AI-style phrasing" for f in flags)
