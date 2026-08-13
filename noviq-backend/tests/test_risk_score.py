from app.models.analysis import RiskLevel
from app.services.fraud.risk_score import ComponentScores, classify_risk, compute_fraud_score


def test_all_zero_scores_low_risk():
    score = compute_fraud_score(ComponentScores())
    assert score == 0
    assert classify_risk(score) == RiskLevel.LOW


def test_all_max_scores_high_risk():
    score = compute_fraud_score(
        ComponentScores(
            experience_score=100,
            education_score=100,
            skill_score=100,
            keyword_stuffing_score=100,
            formatting_score=100,
            timeline_score=100,
            ai_score=100,
            duplicate_score=100,
        )
    )
    assert score == 100
    assert classify_risk(score) == RiskLevel.HIGH


def test_weights_sum_to_one():
    from app.services.fraud.risk_score import WEIGHTS

    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_medium_risk_band():
    # skill (0.20) + education (0.15) + timeline (0.15) maxed out = 50/100
    score = compute_fraud_score(ComponentScores(skill_score=100, education_score=100, timeline_score=100))
    assert 35 <= score < 65
    assert classify_risk(score) == RiskLevel.MEDIUM
