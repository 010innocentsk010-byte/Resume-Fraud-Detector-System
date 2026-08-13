from app.services.fraud.keyword_stuffing import analyze_keyword_stuffing

NORMAL_TEXT = """
Senior software engineer with five years of professional experience building distributed
backend systems. Led a small team to deliver a new billing platform for an e-commerce
client, improving checkout latency by forty percent through careful database indexing and
caching. Mentored two graduate hires during their first year, and coordinated an on-call
rotation covering payment processing incidents. Previously worked on a recommendation
engine that increased customer retention, and contributed to migrating a monolithic
application toward a set of independently deployable services. Comfortable communicating
technical tradeoffs to non-technical stakeholders and writing clear design documents.
"""

STUFFED_TEXT = """
Python Python Python Python Python Python Machine Learning Machine Learning
Machine Learning Machine Learning Machine Learning Machine Learning Docker Docker
Docker Docker Docker Docker Kubernetes Kubernetes Kubernetes Kubernetes Kubernetes
Kubernetes AWS AWS AWS AWS AWS AWS Python Python Machine Learning Docker Kubernetes
""" * 2


def test_short_text_no_flags():
    score, flags = analyze_keyword_stuffing("Python developer.")
    assert score == 0
    assert flags == []


def test_normal_resume_text_not_flagged():
    score, flags = analyze_keyword_stuffing(NORMAL_TEXT)
    assert score == 0
    assert flags == []


def test_stuffed_text_flagged():
    score, flags = analyze_keyword_stuffing(STUFFED_TEXT)
    assert score > 0
    assert any(f.title == "Keyword stuffing detected" for f in flags)


def test_consecutive_repeats_flagged():
    text = "Experienced experienced experienced experienced engineer with strong backend skills " * 3
    score, flags = analyze_keyword_stuffing(text)
    assert any(f.title == "Repeated consecutive keywords" for f in flags)
