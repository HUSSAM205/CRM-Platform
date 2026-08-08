# CRM / Document Collaboration Platform

A full-stack CRM and document collaboration platform with separate Admin and User portals, RBAC, file management, comments, messaging, notifications, audit logs, dashboards, and AI-powered semantic search.

See [`docs/architecture.md`](docs/architecture.md) for the complete architecture and database schema.

## Features

- **Auth & RBAC** — JWT access + rotating refresh tokens in httpOnly cookies, CSRF protection, Argon2id password hashing, seeded system roles (admin/manager/member/viewer) with a static permission catalog, plus resource-level document sharing on top of org-tier role permissions.
- **Documents** — upload/download/versioning, per-user or per-role sharing at view/comment/edit/manage levels, soft delete, Postgres full-text search.
- **Comments** — threaded, @mentions, tombstoned on delete so reply threads never orphan.
- **Messaging** — direct messages with realtime delivery over WebSocket.
- **Notifications** — in-app, realtime, fanned out on mentions, comments, and new messages.
- **Audit log & dashboard** — every mutating action recorded; admin-only full audit trail plus an org-wide activity feed and summary metrics.
- **AI semantic search** — `sentence-transformers` embeddings (PyTorch) blended with keyword search, so natural-language queries with no exact keyword overlap still find the right document.
- **Admin portal** (`/admin/*`) separate from the user portal, gated by the `admin.access` permission.

## Stack

- **Frontend:** Next.js (App Router) + React + TypeScript + Tailwind CSS
- **Backend:** Python + FastAPI (REST API, `/api/v1`)
- **Database:** PostgreSQL (Neon), via SQLAlchemy + Alembic migrations, `pgvector` for embeddings
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

`requirements.txt` includes `torch` + `sentence-transformers` (needed for the semantic search background task) — on a CPU-only machine, install torch from the smaller CPU wheel index first to skip the CUDA build:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-dev.txt
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000.

### 4. AI notebooks (optional — prototyping only, not needed to run the app)

```bash
cd ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/
```

## Testing

```bash
cd backend
pytest
```

Tests run against the real database configured in `backend/.env`, each wrapped in a transaction that's rolled back afterward (see `tests/conftest.py`) — no separate test database needed, and nothing persists.

## Deployment

Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`) and a reference `infra/docker-compose.yml` (self-hosted Postgres + backend + frontend) are provided for a Docker-based deployment. They were authored but **not exercised** in this environment (no Docker available here — local dev uses Neon + `uvicorn`/`next dev` directly instead, see `docs/architecture.md`); review them before relying on them in production. See `infra/.env.example` for the required variables.

## Status

Feature-complete through Phase 6 of the build plan in [`docs/architecture.md`](docs/architecture.md) §9 — polish, backend test suite, rate limiting, and deployment artifacts. The `StorageService` S3 adapter (`backend/app/services/storage_service.py`) is stubbed but not implemented; local-disk storage is used for now.
