from app.services.job_match import compute_skill_overlap


def test_no_jd_skills_returns_zero():
    score, matched, missing = compute_skill_overlap(["python", "sql"], [])
    assert score == 0.0
    assert matched == []
    assert missing == []


def test_full_overlap_scores_100():
    score, matched, missing = compute_skill_overlap(["python", "sql", "docker"], ["python", "sql"])
    assert score == 100.0
    assert matched == ["python", "sql"]
    assert missing == []


def test_partial_overlap():
    score, matched, missing = compute_skill_overlap(["python"], ["python", "sql", "docker", "aws"])
    assert score == 25.0
    assert matched == ["python"]
    assert missing == ["aws", "docker", "sql"]


def test_no_overlap():
    score, matched, missing = compute_skill_overlap(["java"], ["python", "sql"])
    assert score == 0.0
    assert matched == []
    assert missing == ["python", "sql"]
