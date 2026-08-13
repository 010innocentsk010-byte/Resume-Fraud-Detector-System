"""Orchestrates the full fraud-detection pipeline for a single resume:
runs every detector module, aggregates the risk score, and persists an
Analysis (+ initial Report) row.
"""
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.analysis import Analysis
from app.models.report import Report
from app.models.resume import Resume, ResumeStatus
from app.schemas.resume import ParsedResume
from app.services.ai_section_detector import analyze_ai_by_section
from app.services.ats_scorer import analyze_ats_score
from app.services.fraud import ai_text_detection, duplicate_detection, education, formatting, keyword_stuffing, skills, timeline
from app.services.fraud.risk_score import ComponentScores, build_recommendation, classify_risk, compute_fraud_score

logger = get_logger(__name__)


def run_analysis(db: Session, resume: Resume) -> Analysis:
    if not resume.raw_text or not resume.parsed_data:
        raise ValueError("Resume must be parsed before analysis can run")

    parsed = ParsedResume.model_validate(resume.parsed_data)
    raw_text = resume.raw_text

    resume.status = ResumeStatus.ANALYZING
    db.add(resume)
    db.flush()

    all_flags = []

    timeline_score, timeline_flags = timeline.analyze_timeline(parsed)
    all_flags += timeline_flags

    education_score, education_flags = education.analyze_education(parsed)
    all_flags += education_flags

    skill_score, skill_flags = skills.analyze_skills(parsed)
    all_flags += skill_flags

    keyword_score, keyword_flags = keyword_stuffing.analyze_keyword_stuffing(raw_text)
    all_flags += keyword_flags

    formatting_score, formatting_flags = formatting.analyze_formatting(raw_text, parsed)
    all_flags += formatting_flags

    ai_score, ai_flags = ai_text_detection.analyze_ai_generated(raw_text)
    all_flags += ai_flags

    duplicate_score, duplicate_flags = duplicate_detection.find_duplicates(
        db, resume.id, raw_text, resume.text_fingerprint or duplicate_detection.compute_fingerprint(raw_text)
    )
    all_flags += duplicate_flags

    # ATS score and per-section AI detection are parallel, non-fraud signals —
    # they are surfaced to the UI directly and intentionally excluded from
    # all_flags / ComponentScores / fraud_score below.
    ats_score, ats_issues = analyze_ats_score(raw_text, parsed)
    ai_section_scores = analyze_ai_by_section(raw_text)

    # Experience score derives from timeline + skill-evidence signals — there is no
    # standalone "experience" detector, it's a blended read of those two axes.
    experience_score = round(timeline_score * 0.6 + skill_score * 0.4, 1)

    component_scores = ComponentScores(
        experience_score=experience_score,
        education_score=education_score,
        skill_score=skill_score,
        keyword_stuffing_score=keyword_score,
        formatting_score=formatting_score,
        timeline_score=timeline_score,
        ai_score=ai_score,
        duplicate_score=duplicate_score,
    )
    fraud_score = compute_fraud_score(component_scores)
    risk_level = classify_risk(fraud_score)
    recommendation = build_recommendation(fraud_score, risk_level, all_flags)

    analysis = Analysis(
        resume_id=resume.id,
        experience_score=experience_score,
        education_score=education_score,
        skill_score=skill_score,
        formatting_score=formatting_score,
        timeline_score=timeline_score,
        ai_score=ai_score,
        keyword_stuffing_score=keyword_score,
        duplicate_score=duplicate_score,
        fraud_score=fraud_score,
        risk_level=risk_level,
        flags=[f.model_dump() for f in all_flags],
        ats_score=ats_score,
        ats_issues=[f.model_dump() for f in ats_issues],
        ai_section_scores=[s.model_dump() for s in ai_section_scores],
        details={
            "weights": {
                "experience_score": 0.15,
                "education_score": 0.15,
                "skill_score": 0.20,
                "keyword_stuffing_score": 0.10,
                "formatting_score": 0.10,
                "timeline_score": 0.15,
                "ai_score": 0.10,
                "duplicate_score": 0.05,
            },
            "skills_claimed": parsed.skills,
            "sections_found": parsed.sections_found,
        },
    )
    db.add(analysis)
    db.flush()

    report = Report(analysis_id=analysis.id, recommendation=recommendation, pdf_path="")
    db.add(report)

    resume.status = ResumeStatus.ANALYZED
    db.add(resume)

    db.commit()
    db.refresh(analysis)

    logger.info("Analysis complete for resume %s: fraud_score=%.1f risk=%s", resume.id, fraud_score, risk_level.value)
    return analysis
