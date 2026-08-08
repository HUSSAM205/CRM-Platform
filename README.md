# CRM / Document Collaboration Platform

A full-stack CRM and document collaboration platform with separate Admin and User portals, RBAC, file management, comments, messaging, notifications, audit logs, dashboards, and AI-powered semantic search.

See [`docs/architecture.md`](docs/architecture.md) for the complete architecture, database schema, and implementation plan.

## Stack

- **Frontend:** Next.js (App Router) + React + TypeScript + Tailwind CSS
- **Backend:** Python + FastAPI (REST API, `/api/v1`)
- **Database:** PostgreSQL (Neon), via SQLAlchemy + Alembic migrations
- **AI/Data:** PyTorch (`sentence-transformers`) + Jupyter notebooks

## Project layout

```
frontend/   Next.js app (Admin portal + User portal, one codebase)
backend/    FastAPI app
ai/         PyTorch embedding module + Jupyter notebooks
infra/      Deployment reference (docker-compose, env docs)
docs/       Architecture documentation
```

## Local development

### 1. Database (Neon)

1. Create a free project at [neon.tech](https://neon.tech).
2. Copy the connection string and set it as `DATABASE_URL` in `backend/.env` (use the `postgresql+psycopg://` scheme — see `backend/.env.example`).

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env   # then fill in DATABASE_URL, JWT_SECRET, REFRESH_SECRET
alembic upgrade head
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000 — health check at `/api/v1/health`, interactive docs at `/api/v1/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000.

### 4. AI module (only needed once Phase 5 semantic search is in use)

```bash
cd ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/
```

## Status

Under active development — see [`docs/architecture.md`](docs/architecture.md) §9 for the phase-by-phase build plan and current progress.
