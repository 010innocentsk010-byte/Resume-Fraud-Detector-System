"""End-to-end scenario tests: run realistic resume text through the actual
parsing + detector pipeline (the same composition analysis_engine.run_analysis
uses) and assert on the final risk level / AI likelihood / job-match outcome,
rather than on synthetic component scores like the other fraud-detector unit
tests. Duplicate-submission detection is excluded — it requires a live DB
session to compare against previously stored resumes, which none of these
fixtures represent.

See TESTING.md for the full write-up of each scenario and its observed result.
"""
from app.models.analysis import RiskLevel
from app.models.resume import Resume
from app.services.fraud import ai_text_detection, education, formatting, keyword_stuffing, skills, timeline
from app.services.fraud.risk_score import ComponentScores, classify_risk, compute_fraud_score
from app.services.job_match import analyze_job_match, build_match_recommendation
from app.services.resume_parser import parse_resume_text
from tests.fixtures.sample_resumes import (
    AI_BUZZWORD_RESUME,
    FABRICATED_RESUME,
    GENUINE_RESUME,
    SAMPLE_JOB_DESCRIPTION,
    STRONG_MATCH_RESUME,
    UNREALISTIC_EDUCATION_RESUME,
    UNRELATED_JOB_DESCRIPTION,
)


def _run_pipeline(raw_text: str):
    """Mirrors analysis_engine.run_analysis's composition, minus duplicate
    detection (needs a DB session) — same detectors, same weighting."""
    parsed = parse_resume_text(raw_text)

    timeline_score, timeline_flags = timeline.analyze_timeline(parsed)
    education_score, education_flags = education.analyze_education(parsed)
    skill_score, skill_flags = skills.analyze_skills(parsed)
    keyword_score, keyword_flags = keyword_stuffing.analyze_keyword_stuffing(raw_text)
    formatting_score, formatting_flags = formatting.analyze_formatting(raw_text, parsed)
    ai_score, ai_flags = ai_text_detection.analyze_ai_generated(raw_text)
    experience_score = round(timeline_score * 0.6 + skill_score * 0.4, 1)

    fraud_score = compute_fraud_score(
        ComponentScores(
            experience_score=experience_score,
            education_score=education_score,
            skill_score=skill_score,
            keyword_stuffing_score=keyword_score,
            formatting_score=formatting_score,
            timeline_score=timeline_score,
            ai_score=ai_score,
            duplicate_score=0.0,
        )
    )
    return {
        "parsed": parsed,
        "fraud_score": fraud_score,
        "risk_level": classify_risk(fraud_score),
        "education_score": education_score,
        "education_flags": education_flags,
        "ai_score": ai_score,
        "ai_flags": ai_flags,
        "timeline_flags": timeline_flags,
    }


def test_genuine_resume_is_low_risk():
    result = _run_pipeline(GENUINE_RESUME)
    assert result["risk_level"] == RiskLevel.LOW
    assert result["fraud_score"] < 35


def test_fabricated_resume_with_compounding_signals_is_high_risk():
    # Overlapping full-time jobs, impossible degree durations, unsupported
    # skill claims, keyword stuffing, hidden characters, and AI-style
    # phrasing all in one resume — the "would be caught" adversarial case.
    result = _run_pipeline(FABRICATED_RESUME)
    assert result["risk_level"] == RiskLevel.HIGH
    assert result["fraud_score"] >= 65
    flagged_categories = {f.category for f in result["timeline_flags"]}
    assert "timeline" in flagged_categories


def test_unrealistic_education_duration_is_flagged_but_not_high_risk_alone():
    # A single isolated quirk (one degree completed in an implausibly short
    # time) is detected and scored, but the weighted model intentionally
    # requires multiple correlated signals before overall risk reaches
    # Medium/High — this prevents one quirky detector from producing a false
    # alarm. See TESTING.md for the worked-out reasoning.
    result = _run_pipeline(UNREALISTIC_EDUCATION_RESUME)
    genuine = _run_pipeline(GENUINE_RESUME)
    assert result["education_score"] > 0
    assert any(f.title == "Unrealistic program duration" for f in result["education_flags"])
    assert result["fraud_score"] > genuine["fraud_score"]
    assert result["risk_level"] == RiskLevel.LOW


def test_ai_buzzword_resume_has_high_ai_likelihood():
    result = _run_pipeline(AI_BUZZWORD_RESUME)
    assert result["ai_score"] >= 50
    assert any(f.title == "High density of generic/AI-style phrasing" for f in result["ai_flags"])


def test_strong_match_resume_scores_high_against_matching_job():
    parsed = parse_resume_text(STRONG_MATCH_RESUME)
    resume = Resume(raw_text=STRONG_MATCH_RESUME, parsed_data=parsed.model_dump())

    match = analyze_job_match(resume, SAMPLE_JOB_DESCRIPTION)
    assert match.match_score >= 75
    assert build_match_recommendation(match.match_score) == "Strong Candidate"

    unrelated_match = analyze_job_match(resume, UNRELATED_JOB_DESCRIPTION)
    assert unrelated_match.match_score < match.match_score
    assert build_match_recommendation(unrelated_match.match_score) == "Weak Candidate"
