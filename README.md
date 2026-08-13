# Noviq Intelligence

### AI Resume Fraud Detection System

A production-grade web application that analyzes uploaded resumes (PDF/DOCX), detects fraud
indicators (timeline inconsistencies, skill exaggeration, education inconsistencies, keyword
stuffing, AI-generated text, duplicate submissions), produces a 0-100 fraud risk score with
explanations, and gives recruiters a dashboard and downloadable PDF reports.

## Architecture

```
.
├── noviq-backend/     FastAPI + SQLAlchemy + PostgreSQL + spaCy / Sentence-Transformers
├── noviq-frontend/    Next.js 14 (App Router) + TypeScript + Tailwind CSS + Framer Motion
└── docker-compose.yml
```

## Tech stack

| Layer          | Choice                                                            |
|----------------|--------------------------------------------------------------------|
| Frontend       | Next.js, TypeScript, Tailwind CSS, Framer Motion, Recharts        |
| Backend        | Python, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2              |
| Database       | PostgreSQL                                                          |
| Auth           | JWT (access + refresh tokens), bcrypt password hashing             |
| AI / NLP       | spaCy (NER), Sentence-Transformers (semantic similarity), heuristic AI-text detector — fully local, no API key required |
| File storage   | Local disk by default, pluggable S3-compatible backend             |
| Reports        | Server-rendered PDF via WeasyPrint                                  |

## Quick start (Docker)

```bash
cp noviq-backend/.env.example noviq-backend/.env
cp noviq-frontend/.env.example noviq-frontend/.env.local
docker compose up --build
```

- API: http://localhost:8000  (docs at `/api/docs`)
- Frontend: http://localhost:3000
- Postgres: localhost:5432

## Quick start (manual / local dev)

### Backend

```bash
cd noviq-backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
copy .env.example .env          # then edit DATABASE_URL etc.
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd noviq-frontend
npm install
copy .env.example .env.local
npm run dev
```

Default seeded admin account (created by `noviq-backend/app/db/seed.py`, run with
`python -m app.db.seed`): `admin@example.com` / `ChangeMe123!`

## Project layout

See `noviq-backend/README.md` and `noviq-frontend/README.md` for module-level detail, and
`docs/API.md` for the endpoint reference (also available live via Swagger/OpenAPI at
`/api/docs` once the backend is running).

## Fraud detection modules

| Module                  | Location                                              |
|--------------------------|--------------------------------------------------------|
| Resume parsing           | `noviq-backend/app/services/resume_parser.py`                |
| Timeline analysis        | `noviq-backend/app/services/fraud/timeline.py`                |
| Education analysis       | `noviq-backend/app/services/fraud/education.py`                |
| Skills analysis          | `noviq-backend/app/services/fraud/skills.py`                  |
| Keyword stuffing         | `noviq-backend/app/services/fraud/keyword_stuffing.py`          |
| AI-generated text        | `noviq-backend/app/services/fraud/ai_text_detection.py`          |
| Duplicate detection       | `noviq-backend/app/services/fraud/duplicate_detection.py`        |
| Risk score aggregation   | `noviq-backend/app/services/fraud/risk_score.py`                |
| Report generation        | `noviq-backend/app/services/report_generator.py`                |

## License

Proprietary — built for academic dissertation / internal use.
