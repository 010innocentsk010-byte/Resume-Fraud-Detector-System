from app.schemas.resume import ParsedEducationEntry, ParsedExperienceEntry, ParsedResume
from app.services.fraud.timeline import analyze_timeline


def _resume(experience=None, education=None) -> ParsedResume:
    return ParsedResume(
        contact={}, skills=[], education=education or [], experience=experience or [], sections_found=[]
    )


def test_no_experience_no_flags():
    score, flags = analyze_timeline(_resume())
    assert score == 0
    assert flags == []


def test_invalid_date_range_flagged():
    exp = ParsedExperienceEntry(start_date="2020", end_date="2018", is_current=False, raw_text="Acme 2020-2018")
    score, flags = analyze_timeline(_resume(experience=[exp]))
    assert score > 0
    assert any(f.title == "Invalid employment date range" for f in flags)


def test_overlapping_jobs_flagged():
    exp1 = ParsedExperienceEntry(start_date="2018", end_date="2021", is_current=False, raw_text="Job A 2018-2021")
    exp2 = ParsedExperienceEntry(start_date="2019", end_date="2022", is_current=False, raw_text="Job B 2019-2022")
    score, flags = analyze_timeline(_resume(experience=[exp1, exp2]))
    assert score > 0
    assert any(f.title == "Overlapping employment periods" for f in flags)


def test_employment_overlapping_full_time_study_flagged():
    exp = ParsedExperienceEntry(start_date="2018", end_date="2022", is_current=False, raw_text="Google 2018-2022")
    edu = ParsedEducationEntry(start_year=2018, end_year=2022, raw_text="Bachelor 2018-2022")
    score, flags = analyze_timeline(_resume(experience=[exp], education=[edu]))
    assert score > 0
    assert any(f.title == "Possible timeline inconsistency" for f in flags)


def test_clean_non_overlapping_history_scores_low():
    exp1 = ParsedExperienceEntry(start_date="2015", end_date="2018", is_current=False, raw_text="Job A 2015-2018")
    exp2 = ParsedExperienceEntry(start_date="2018", end_date="2021", is_current=False, raw_text="Job B 2018-2021")
    score, flags = analyze_timeline(_resume(experience=[exp1, exp2]))
    assert score == 0
    assert flags == []
