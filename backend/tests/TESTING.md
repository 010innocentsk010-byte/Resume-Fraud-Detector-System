# Test dataset & observed results

`tests/test_end_to_end_scenarios.py` runs five hand-written resumes
(`tests/fixtures/sample_resumes.py`) through the real parsing + detector
pipeline — the same composition `analysis_engine.run_analysis` uses (minus
duplicate-submission detection, which needs a live database to compare
against). Every number below is the actual output of running the fixture
through the code, not a hand-estimate — regex-driven detectors are too
sensitive to exact wording/dates to predict by hand reliably.

## Scenarios

| Scenario | Fixture | Result | Expectation |
|---|---|---|---|
| Genuine resume | `GENUINE_RESUME` | fraud score **0.0** — Low Risk | Low Risk |
| Fabricated resume (compounding signals) | `FABRICATED_RESUME` | fraud score **69.5** — High Risk | High Risk |
| Unrealistic education duration | `UNREALISTIC_EDUCATION_RESUME` | fraud score **3.0** — Low Risk, but `education_score=20` and the "Unrealistic program duration" flag fires | Flag detected |
| AI-generated writing style | `AI_BUZZWORD_RESUME` | `ai_score=50` — flags: "High density of generic/AI-style phrasing", "Unusually uniform sentence structure" | High AI likelihood |
| Strong job match | `STRONG_MATCH_RESUME` vs. a matching Senior Backend Engineer JD | `match_score=88.5`, matched skills `aws, ci/cd, docker, graphql, kubernetes, postgresql, python`, recommendation **Strong Candidate** | High match |
| Same resume vs. an unrelated JD | `STRONG_MATCH_RESUME` vs. a Registered Nurse JD | `match_score=5.0`, recommendation **Weak Candidate** | Low match (control) |

## A note on the unrealistic-education scenario

The original expectation for "unrealistic experience/education" was
Medium/High risk. Running it through the real scorer, a single isolated
detector firing at its maximum realistic severity **cannot** reach the
Medium threshold (35) on its own — the risk-score weights
(`app/services/fraud/risk_score.py::WEIGHTS`) cap any one category's
contribution well under that (education is weighted 0.15; even a maxed-out
`education_score=100` only contributes 15 points). This is intentional: it
stops one quirky/false-positive detector from tipping a candidate into
"Medium risk" by itself. Overall risk only climbs once multiple independent
signals agree — which is what `FABRICATED_RESUME` demonstrates: overlapping
full-time jobs, two implausibly short degrees, an overlapping degree pair,
unsupported skill claims, keyword stuffing, hidden Unicode characters, and
AI-style phrasing together push the score from ~3 to ~70.

The test for this scenario (`test_unrealistic_education_duration_is_flagged_but_not_high_risk_alone`)
asserts on the detector-level output — the flag fires and the score is
higher than the genuine baseline — rather than forcing an unrelated second
signal into the fixture just to cross an aggregate threshold.

## Running these tests

```
cd backend
.venv\Scripts\python.exe -m pytest tests/test_end_to_end_scenarios.py -v
```

They're pure-function tests (no database, no model downloads beyond the
already-cached spaCy/Sentence-Transformer models used elsewhere in the
suite) and run in well under a second alongside the rest of `pytest`.
