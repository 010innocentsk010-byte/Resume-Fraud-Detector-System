# Noviq Intelligence

### AI Resume Fraud Detection System

A production-grade web application that analyzes uploaded resumes (PDF/DOCX), detects fraud
indicators (timeline inconsistencies, skill exaggeration, education inconsistencies, keyword
stuffing, AI-generated text, duplicate submissions), produces a 0-100 fraud risk score with
explanations, and gives recruiters a dashboard and downloadable PDF reports.

## Architecture

```
.
├── backend/     FastAPI + SQLAlchemy + PostgreSQL + spaCy / Sentence-Transformers
├── frontend/    Next.js 14 (App Router) + TypeScript + Tailwind CSS + Framer Motion
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
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

- API: http://localhost:8000  (docs at `/api/docs`)
- Frontend: http://localhost:3000
- Postgres: localhost:5432

## Quick start (manual / local dev)

### Backend

```bash
cd backend
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
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Default seeded admin account (created by `backend/app/db/seed.py`, run with
`python -m app.db.seed`): `admin@example.com` / `ChangeMe123!`

## Project layout

See `backend/README.md` and `frontend/README.md` for module-level detail, and
`docs/API.md` for the endpoint reference (also available live via Swagger/OpenAPI at
`/api/docs` once the backend is running).

## Fraud detection modules

| Module                  | Location                                              |
|--------------------------|--------------------------------------------------------|
| Resume parsing           | `backend/app/services/resume_parser.py`                |
| Timeline analysis        | `backend/app/services/fraud/timeline.py`                |
| Education analysis       | `backend/app/services/fraud/education.py`                |
| Skills analysis          | `backend/app/services/fraud/skills.py`                  |
| Keyword stuffing         | `backend/app/services/fraud/keyword_stuffing.py`          |
| AI-generated text        | `backend/app/services/fraud/ai_text_detection.py`          |
| Duplicate detection       | `backend/app/services/fraud/duplicate_detection.py`        |
| Risk score aggregation   | `backend/app/services/fraud/risk_score.py`                |
| Report generation        | `backend/app/services/report_generator.py`                |

## License

Proprietary — built for academic dissertation / internal use.
