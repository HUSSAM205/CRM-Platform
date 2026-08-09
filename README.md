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

Deployed as: **Render** (backend) + **Vercel** (frontend) + **Neon** (database, already in use for dev too). This is a monorepo, so both platforms need care about which subfolder they build from.

### 1. Backend → Render

The backend imports the sibling `ai/` package at startup (`backend/app/ai/embedding_client.py`, shared with the notebook — see `docs/architecture.md`). Render restricts a service to files *inside* its configured Root Directory, so **do not** set Root Directory to `backend` — that would hide `ai/` from it and the app would fail to start. Instead, leave Root Directory as the repo root and reference `backend/` explicitly in the commands:

1. [render.com](https://render.com) → **New +** → **Web Service** → connect the `CRM-Platform` GitHub repo.
2. **Root Directory:** leave blank (repo root)
3. **Runtime:** Python 3
4. **Build Command:** `pip install -r backend/requirements.txt`
5. **Start Command:** `cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Environment variables:**
   | Key | Value |
   |---|---|
   | `ENVIRONMENT` | `production` |
   | `DEBUG` | `false` |
   | `DATABASE_URL` | your Neon connection string (`postgresql+psycopg://...`) |
   | `JWT_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `REFRESH_SECRET` | (same, a different value) |
   | `CORS_ORIGINS` | `["https://your-app.vercel.app"]` — fill in after step 2, then redeploy |
   | `STORAGE_BACKEND` | `local` |
   | `LOCAL_STORAGE_PATH` | `./data/uploads` |
7. Create the service, note its URL (`https://your-backend.onrender.com`).

**Known risks on Render's free tier:** the build installs `torch` + `sentence-transformers` (large — may hit build time limits), and loading the embedding model at runtime needs real memory (may hit the 512MB RAM cap on the free instance type). If the AI dependency causes build/OOM failures, the fastest fix is commenting `torch`/`sentence-transformers` out of `backend/requirements.txt` for this deploy — keyword search still works fully without them (`/search/semantic` degrades to keyword-only automatically, see `backend/app/api/v1/search.py`). Also: free-tier disk is **not persistent** — uploaded files won't survive a redeploy/restart (same tradeoff as GradTrack's Render setup).

### 2. Frontend → Vercel

1. [vercel.com](https://vercel.com) → **Add New** → **Project** → import the same GitHub repo.
2. **Root Directory:** `frontend`
3. Framework preset: Next.js (auto-detected).
4. **Environment variable:** `NEXT_PUBLIC_API_URL` = the Render backend URL from step 1.
5. Deploy, note the resulting URL (`https://your-app.vercel.app`).

### 3. Close the loop

Go back to the Render backend's env vars, set `CORS_ORIGINS` to `["https://your-app.vercel.app"]` (the real Vercel URL), and redeploy the backend. Frontend and backend are on different domains in this setup — cookies are configured `SameSite=None; Secure` in production specifically to support that (see `backend/app/api/v1/auth.py` and `backend/app/core/csrf.py`), so this cross-origin flow is expected to work, not a workaround.

### Docker (alternative, self-hosted)

Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`) and a reference `infra/docker-compose.yml` (self-hosted Postgres + backend + frontend) are also provided. They were authored but **not exercised** in this environment (no Docker available here); review them before relying on them in production. See `infra/.env.example` for the required variables.

## Status

Feature-complete through Phase 6 of the build plan in [`docs/architecture.md`](docs/architecture.md) §9 — polish, backend test suite, rate limiting, and deployment artifacts. The `StorageService` S3 adapter (`backend/app/services/storage_service.py`) is stubbed but not implemented; local-disk storage is used for now.
