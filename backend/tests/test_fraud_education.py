from app.schemas.resume import ParsedEducationEntry, ParsedResume
from app.services.fraud.education import analyze_education


def _resume(education) -> ParsedResume:
    return ParsedResume(contact={}, skills=[], education=education, experience=[], sections_found=[])


def test_no_education_no_flags():
    score, flags = analyze_education(_resume([]))
    assert score == 0
    assert flags == []


def test_impossible_bachelor_duration():
    # A one-year "Bachelor" claim is shorter than any realistic full-time program.
    bachelor = ParsedEducationEntry(degree="Bachelor", start_year=2019, end_year=2020, raw_text="Bachelor 2019-2020")
    score, flags = analyze_education(_resume([bachelor]))
    assert score > 0
    assert any(f.title == "Unrealistic program duration" for f in flags)


def test_realistic_bachelor_timeline_no_flag():
    bachelor = ParsedEducationEntry(degree="Bachelor", start_year=2016, end_year=2020, raw_text="Bachelor 2016-2020")
    score, flags = analyze_education(_resume([bachelor]))
    assert score == 0
    assert flags == []


def test_invalid_date_range_flagged():
    bad = ParsedEducationEntry(degree="Master", start_year=2022, end_year=2020, raw_text="Master 2022-2020")
    score, flags = analyze_education(_resume([bad]))
    assert score > 0
    assert any(f.title == "Invalid education date range" for f in flags)


def test_overlapping_degrees_flagged():
    first = ParsedEducationEntry(degree="Bachelor", start_year=2015, end_year=2019, raw_text="Bachelor 2015-2019")
    second = ParsedEducationEntry(degree="Master", start_year=2016, end_year=2018, raw_text="Master 2016-2018")
    score, flags = analyze_education(_resume([first, second]))
    assert score > 0
    assert any(f.title == "Overlapping full-time degree programs" for f in flags)
