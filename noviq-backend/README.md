# Backend — Noviq Intelligence

### AI Resume Fraud Detection System

FastAPI service providing authentication, resume upload/parsing, the fraud-detection
engine, dashboards, and PDF report generation.

## Layout

```
app/
├── main.py                 FastAPI app, middleware, exception handlers
├── core/                   settings, JWT/password security, logging
├── db/                     SQLAlchemy session, declarative base, seed script
├── models/                 SQLAlchemy ORM models (users, applicants, resumes, analysis, reports)
├── schemas/                Pydantic request/response models
├── api/v1/                 route handlers (auth, applicants, resumes, analysis, reports, dashboard, admin)
├── services/
│   ├── storage.py          pluggable local-disk / S3 file storage
│   ├── text_extraction.py  PDF/DOCX -> raw text (pdfplumber, python-docx)
│   ├── resume_parser.py    raw text -> structured ParsedResume (regex + spaCy NER)
│   ├── nlp.py               lazy-loaded spaCy / Sentence-Transformer singletons
│   ├── analysis_engine.py  orchestrates every fraud detector into one Analysis record
│   ├── report_generator.py Jinja2 + WeasyPrint PDF report rendering
│   └── fraud/               one module per detector (timeline, education, skills,
│                             keyword_stuffing, formatting, ai_text_detection,
│                             duplicate_detection) + risk_score.py aggregator
└── templates/report.html    PDF report template
alembic/                     database migrations
tests/                       pytest unit tests for parsing + every fraud detector
```

## Running tests

```bash
pip install -r requirements.txt
pytest
```

The fraud-detection and parsing tests (`tests/test_fraud_*.py`, `tests/test_resume_parser.py`,
`tests/test_risk_score.py`) are pure unit tests with no database or model-download
dependency — they run in well under a second and are the fastest way to verify a change
to the detection logic didn't break anything.

## Adding a new fraud signal

1. Add a module under `app/services/fraud/` exposing `analyze_x(...) -> tuple[float, list[FraudFlag]]`
   (score 0-100, higher = more suspicious).
2. Wire it into `services/analysis_engine.py::run_analysis`.
3. Add its weight to `services/fraud/risk_score.py::WEIGHTS` (weights must sum to 1.0 —
   `tests/test_risk_score.py::test_weights_sum_to_one` enforces this).
4. Add a column to the `Analysis` model + an Alembic migration if it needs its own
   persisted score.

## API docs

Once running: Swagger UI at `/api/docs`, ReDoc at `/api/redoc`, raw OpenAPI schema at
`/api/openapi.json`.
