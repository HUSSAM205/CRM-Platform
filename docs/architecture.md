# CRM / Document-Collaboration Platform — Architecture & Implementation Plan

## Context

The user wants a production-quality, full-stack CRM/document-collaboration platform built from scratch: Next.js/TypeScript/Tailwind frontend, Python/FastAPI backend, PostgreSQL database, PyTorch/Jupyter AI layer — with separate Admin and User portals, RBAC, file management, comments, messaging, notifications, audit logs, dashboards, and search. This is unrelated to the existing GradTrack CRM project in `C:\Users\hossa\Downloads\claude` (Express/SQLite) — the user explicitly chose to build this as a new, separate project.

**Target directory:** `C:\Users\hossa\Downloads\new-crm` (renamed from the initial `new crm` during Phase 0 — spaces in the path caused quoting failures in the Windows dev-server tooling).

**Environment constraint discovered during planning:** this machine has Node v24 and Python 3.12, but **no Docker**. This rules out a docker-compose-based local Postgres/MinIO setup for day-to-day dev. Resolved with the user:
- **Postgres:** free-tier **Neon** (serverless, supports the `pgvector` extension needed for AI semantic search). The user will create the Neon project and hand me a `DATABASE_URL`.
- **File storage:** local disk for dev, behind an S3-shaped storage interface so it's a one-config-change swap to real S3/R2 in production. No MinIO/Docker dependency now.
- Dockerfiles/compose are still authored (Phase 6, deployment prep) as artifacts for future deployment, but local dev does **not** depend on Docker being installed — backend runs via `uvicorn`, frontend via `next dev`, both directly.

Everything else below reflects decisions made deliberately (one approach per decision, not a menu), designed to be implemented incrementally in testable phases.

---

## 1. High-Level Architecture

- **One Next.js app**, App Router, with an `admin/` segment (real URL prefix, so admin pages live at `/admin/*`), plus `(portal)` and `(auth)` route groups (organizational only — Next.js strips parenthesized segments from the URL, so portal pages live at the root, e.g. `/dashboard`) — two portals, one codebase, shared component/design-system library and shared auth/session logic.
- **One FastAPI backend**, versioned REST API under `/api/v1`, with role- and resource-level permission dependencies enforced per route/router.
- **PostgreSQL (Neon)** as system of record, including native full-text search (`tsvector`/GIN) — no separate search engine — plus `pgvector` for AI semantic search.
- **Local-disk file storage** in dev behind an S3-shaped `StorageService` interface (swap to S3/R2 in prod via config only).
- **Auth:** JWT access token (short-lived) + rotating refresh token (long-lived), both in httpOnly cookies, plus a CSRF header for mutating requests.
- **AI feature: semantic document search** — pretrained sentence-transformer (PyTorch), prototyped in a Jupyter notebook, embeddings stored via `pgvector`, served from FastAPI, blended with keyword full-text search.

---

## 2. Monorepo Folder Structure

```
new crm/
├── frontend/                          # Next.js App Router app (both portals)
│   ├── src/
│   │   ├── app/
│   │   │   ├── (portal)/              # User/public portal
│   │   │   │   ├── layout.tsx         # Portal shell + user auth gate
│   │   │   │   ├── dashboard/
│   │   │   │   ├── documents/[documentId]/
│   │   │   │   ├── messages/
│   │   │   │   ├── notifications/
│   │   │   │   ├── search/
│   │   │   │   └── settings/profile/
│   │   │   ├── admin/                 # Admin portal (real segment -> /admin/*, not a route group)
│   │   │   │   ├── layout.tsx         # Admin shell + admin/manager auth gate
│   │   │   │   ├── users/ roles/ audit-log/ analytics/ org-settings/
│   │   │   ├── (auth)/                # Unauthenticated: login/register/invite/forgot-password
│   │   │   └── layout.tsx             # Root layout, theme provider
│   │   ├── components/
│   │   │   ├── ui/                    # Radix + Tailwind primitives (design system)
│   │   │   ├── documents/ messaging/ notifications/ charts/
│   │   ├── lib/
│   │   │   ├── api-client.ts          # Typed fetch wrapper, cookie-based, auto-refresh on 401
│   │   │   ├── auth/                  # Session context, useUser(), usePermission()
│   │   │   └── utils/
│   │   ├── types/                     # Mirrors backend Pydantic schemas
│   │   └── styles/globals.css         # Tailwind base + design tokens
│   ├── tailwind.config.ts  next.config.ts  package.json  Dockerfile
│
├── backend/                           # FastAPI app
│   ├── app/
│   │   ├── main.py                    # App factory, middleware, router mounting
│   │   ├── core/                      # config.py (Pydantic Settings), security.py (hashing/JWT), logging.py
│   │   ├── db/                        # base.py, session.py (SQLAlchemy)
│   │   ├── models/                    # SQLAlchemy ORM: user, role, permission, organization,
│   │   │                              #   document, document_version, document_share, tag,
│   │   │                              #   comment, conversation, message, notification,
│   │   │                              #   audit_log, refresh_token
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── api/v1/
│   │   │   ├── router.py              # Aggregates all routers under /api/v1
│   │   │   ├── deps.py                # get_current_user, require_permission, require_document_access
│   │   │   ├── auth.py users.py roles.py documents.py comments.py
│   │   │   ├── messages.py notifications.py audit.py search.py dashboard.py
│   │   │   ├── ws.py                  # WebSocket endpoint for realtime messages/notifications
│   │   │   └── admin/                 # Elevated-only routers, require_permission("admin.access") at router level
│   │   ├── services/                  # Business logic: auth, permission, document, storage,
│   │   │                              #   notification, audit, search services
│   │   └── ai/embedding_client.py     # Thin wrapper calling the `ai` package
│   ├── alembic/  alembic.ini
│   ├── tests/
│   ├── pyproject.toml  Dockerfile
│
├── ai/                                 # PyTorch modules + notebooks, pip-installable
│   ├── notebooks/01_semantic_search_prototype.ipynb
│   ├── ai_core/embeddings.py          # load sentence-transformer, encode(texts) -> vectors
│   ├── requirements.txt  README.md
│
├── infra/
│   ├── docker-compose.yml             # Prod-shaped reference (Postgres+pgvector, backend, frontend) — Phase 6 artifact, not required for local dev
│   ├── .env.example
│
├── docs/architecture.md               # This document, checked into repo
└── README.md
```

---

## 3. Database Schema (PostgreSQL via Alembic)

UUID primary keys (`gen_random_uuid()`), `created_at`/`updated_at TIMESTAMPTZ`. Multi-tenant via `organizations` — every core resource carries `organization_id`.

**Identity & org:** `organizations`, `users` (email, hashed_password [Argon2id], is_active, is_email_verified), `roles` (seeded: admin/manager/member/viewer), `permissions` (static catalog, e.g. `document.create`, `user.invite`), `role_permissions`, `user_roles`, `invitations` (token, expires_at), `refresh_tokens` (token_hash, family_id for rotation/reuse-detection, revoked_at, replaced_by_id).

**Documents:** `documents` (title, storage_key, mime_type, current_version_id, folder_id, is_deleted soft-delete, `search_vector TSVECTOR` generated column), `document_versions` (append-only), `folders` (self-referencing hierarchy), `tags` + `document_tags`, `document_shares` (grantee_type ENUM user/role, grantee_id, permission ENUM view/comment/edit/manage — this is the **resource-level** grant table), `document_embeddings` (`embedding VECTOR(384)`, pgvector).

**Comments:** `comments` (self-referencing `parent_comment_id` for threading), `comment_mentions`.

**Messaging:** `conversations` (type direct/channel), `conversation_members` (`last_read_at` drives unread counts), `messages`.

**Notifications:** `notifications` (type ENUM, `payload JSONB`, is_read).

**Audit:** `audit_log` (actor_id nullable, action, resource_type, resource_id, `metadata JSONB`) — append-only, never updated/deleted.

**Key indexes:** GIN on `documents.search_vector`; composite `documents(organization_id, is_deleted)`; `document_shares(document_id, grantee_type, grantee_id)`; `audit_log(organization_id, created_at DESC)` and `audit_log(resource_type, resource_id)`; `notifications(user_id, is_read, created_at DESC)`; `messages(conversation_id, created_at)`; `refresh_tokens(token_hash)` unique + `refresh_tokens(family_id)`; pgvector index on `document_embeddings.embedding` (exact scan fine at demo scale, ivfflat/hnsw noted for later).

---

## 4. Authentication & Authorization

- **Tokens:** JWT access token (15 min, stateless) + rotating refresh token (7–30 day, stateful) — stateless access avoids a DB hit per request; stateful refresh gives revocation + reuse-detection.
- **Transport:** httpOnly, Secure, SameSite=Strict cookies for both tokens (not localStorage/bearer) — avoids XSS-exploitable token storage. CSRF mitigated with a double-submit `X-CSRF-Token` header on mutating requests.
- **Password hashing:** Argon2id (OWASP current default, avoids bcrypt's 72-byte truncation footgun).
- **Refresh rotation:** each refresh issues a new token, marks old one `replaced_by_id`, shared `family_id`. Presenting a revoked/already-replaced token triggers reuse-detection → revoke the whole family, force logout. "Log out all devices" and admin-forced session revocation both hook the same mechanism.
- **RBAC + resource-level permissions (FastAPI dependencies):** `get_current_user` decodes the cookie and loads roles/permissions; `require_permission("document.delete")` is a coarse org-tier role gate; `require_document_access(permission="edit")` is a second, path-param-aware dependency that additionally checks `document_shares` (direct user or role grant, creator always has manage) — both composed on document routes. Every mutating service call writes to `audit_log` from inside the service function (structural, not optional).
- **Admin vs User portal:** one identity system (an org admin is still a `User`). `(admin)` layout does a server-side `require_permission("admin.access")` gate (redirect if absent). Backend: `/admin/*` routers apply `require_permission("admin.access")` at the **router** level so a new admin endpoint can't accidentally ship unguarded.

---

## 5. API Structure (`/api/v1`)

| Router | Prefix | Notes |
|---|---|---|
| auth | `/auth` | login, refresh, logout, register (invite-gated), invitation accept |
| users | `/users` | self-profile, scoped org user read, avatar upload |
| roles | `/roles` | read for all, mutate admin-only |
| documents | `/documents` | CRUD, `/versions`, `/download` (streamed), `/shares` |
| comments | `/documents/{id}/comments` | threaded |
| messages | `/conversations`, `/conversations/{id}/messages` | REST history |
| ws | `/ws` | WebSocket, auth via cookie on upgrade — pushes new messages/notifications |
| notifications | `/notifications` | list, mark read/read-all |
| audit | `/audit-log` | admin/manager only, filterable |
| search | `/search`, `/search/semantic` | keyword FTS, AI-powered (Phase 5) |
| dashboard | `/dashboard/summary`, `/dashboard/activity-feed` | aggregate metrics |
| admin/* | `/admin/users`, `/admin/org-settings`, `/admin/roles` | elevated CRUD, router-level guard |

OpenAPI/Swagger at `/api/v1/docs` (disabled via env flag in prod). `openapi-typescript` codegen adopted in Phase 6 once the schema stabilizes.

---

## 6. Frontend Architecture

- Server Components read the httpOnly cookie directly for the initial gated render (no flash of unauthorized content); a `SessionProvider` context hydrates client components from the root layout's decoded payload. `middleware.ts` does a cheap cookie-presence redirect check before render.
- `api-client.ts`: always `credentials: 'include'`, attaches CSRF header on mutations, transparently retries once through `/auth/refresh` on 401, throws typed `ApiError`.
- Server Components + `fetch` for initial data (lean into RSC); **TanStack Query** for client-side mutations/optimistic updates (comments, messages, notification read-state).
- **Design system:** `components/ui/` built on **Radix UI primitives + Tailwind** (not a pre-themed kit) so 100% of visual styling is custom — this is what avoids the generic-SaaS look. Domain components compose these primitives.
- **Distinctive visual identity:** custom color scale (non-default accent, real dark-mode palette, not inverted grays), distinctive type pairing via `next/font`, bento-grid dashboard rather than uniform card rows, `framer-motion` for panel/list transitions, design tokens defined once in `tailwind.config.ts`/`globals.css`. The `frontend-design` skill will be invoked during actual UI build to sharpen this further.
- **Responsive:** standard Tailwind breakpoints; admin tables collapse to stacked cards below `md`; messaging split-pane collapses to single-pane on mobile.

---

## 7. File Storage

- **Interface:** `StorageService` (async `put`, `get_stream`, `delete`) with a **local-filesystem adapter** for dev (`backend/data/uploads/org/{organization_id}/documents/{document_id}/{version_id}/{filename}`) and an **S3-compatible adapter** (boto3/`aioboto3`) ready for prod — swapped via a `STORAGE_BACKEND=local|s3` env var, no call-site changes.
- **Access pattern:** backend-proxied streaming (`GET /documents/{id}/download` re-checks `document_shares` + role permission on every request, then `StreamingResponse`s the file) — not public/presigned URLs. Slightly more backend bandwidth, but access revocation is instant and every real download is audit-logged, not just URL issuance.

---

## 8. AI/PyTorch Feature — Semantic Document Search

- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, PyTorch-backed, ~80MB, fast CPU inference) — genuinely uses PyTorch (via `sentence-transformers`' `nn.Module`), no GPU dependency needed.
- **Notebook:** `ai/notebooks/01_semantic_search_prototype.ipynb` — loads the model, embeds seed/synthetic document snippets, demonstrates cosine-similarity ranking, compares candidate models. This is the experimentation deliverable.
- **Production path:** `ai/ai_core/embeddings.py` promotes the notebook's working `encode(texts) -> np.ndarray` into a singleton-loaded module, imported by `backend/app/ai/embedding_client.py`. On document create/update, a FastAPI `BackgroundTask` embeds `title + description + text snippet`, stored in `document_embeddings.embedding` (pgvector).
- **Query path:** `/search/semantic?q=` embeds the query, does `ORDER BY embedding <=> :query_embedding LIMIT 20` scoped to org, blended with keyword FTS results in `search_service.py`. If the embedding step errors/is slow, falls back gracefully to keyword-only results — AI is additive, never a hard dependency for core search to function.
- **Dependency:** `CREATE EXTENSION IF NOT EXISTS vector` — confirmed supported on Neon.

---

## 9. Implementation Phases

Each phase boots and is testable end-to-end before moving to the next.

- **Phase 0 — Scaffolding:** repo skeleton, Neon project connected (`DATABASE_URL` from user), FastAPI boots with `/api/v1/health`, Next.js boots with Tailwind + base layout, Alembic initialized with baseline migration, local-disk storage adapter stubbed. *Verify:* backend and frontend both run locally, health check responds, Alembic applies cleanly against Neon.
- **Phase 1 — Auth, users, RBAC:** identity tables + migrations; login/register/invite/refresh/logout; `get_current_user`/`require_permission`; `(auth)` routes + session context + gated `(admin)`/`(portal)` shells. *Verify:* register org owner, invite a member, log in as both, confirm portal-vs-admin route gating.
- **Phase 2 — Documents & files:** document tables + migrations; local-disk storage integration; upload/download/versioning/sharing endpoints; `require_document_access`; Postgres FTS trigger+index; frontend upload/list/detail/download UI. *Verify:* upload, share with one user, confirm an unshared third user gets 403, download works, keyword search finds it.
- **Phase 3 — Comments, messaging, notifications:** comment/conversation/message/notification tables; threaded comments; DM/channel messaging + WebSocket push; notification fan-out (mention, comment, new message); frontend thread UI, inbox, notification bell. *Verify:* a mention triggers a real-time notification; a DM appears without refresh.
- **Phase 4 — Audit log, dashboard, full search:** `audit_log` wired into every mutating service call from Phases 1–3; admin audit UI with filters; dashboard aggregate endpoints + charts; polished `/search` results page (tag/owner/date/type filters). *Verify:* actions across the app show correctly in the audit log; dashboard reflects real counts.
- **Phase 5 — AI semantic search:** `pgvector` migration; notebook; `ai_core` module; background-task embedding on write; `/search/semantic`; hybrid merge; frontend keyword/smart-search toggle. *Verify:* a natural-language query with no exact keyword overlap still surfaces the right document.
- **Phase 6 — Polish & deployment prep:** responsive pass on both portals; loading/error/empty states; pytest (backend services/permissions) + Playwright (login, upload+share, comment+notify, semantic search) E2E tests; OpenAPI→TS codegen; Dockerfiles for both apps + reference `docker-compose.yml`; documented env vars; auth rate limiting; accessibility pass. *Verify:* full test suite passes; app runs end-to-end from a clean checkout per README instructions.

---

## 10. Deployment Prep (artifacts only, not deploying)

- `.env.example` (root) documenting `DATABASE_URL, JWT_SECRET, REFRESH_SECRET, STORAGE_BACKEND, S3_*, CORS_ORIGINS, EMBEDDING_MODEL_NAME`; `backend/app/core/config.py` validates via Pydantic `BaseSettings`.
- Multi-stage Dockerfiles: frontend (`deps → build → next start --standalone`), backend (`deps → uvicorn/gunicorn workers`). Backend entrypoint runs `alembic upgrade head` before serving.
- `infra/docker-compose.yml` as a prod-shaped reference (useful once Docker is available / for real deployment), not required for this machine's local dev loop.
- CORS: `CORSMiddleware` restricted to explicit `CORS_ORIGINS`, `allow_credentials=True`, explicit headers including the CSRF header — never `*` with credentials.
- Secrets: never committed; `.env` gitignored; `.env.example` placeholders only.
- Health checks: `/api/v1/health` (liveness), `/api/v1/health/ready` (DB + storage connectivity).

---

## Critical Files

- `backend/app/api/v1/deps.py` — RBAC + resource-level permission dependencies every protected route composes; gets the security contract right early.
- `backend/alembic/versions/<baseline>` — encodes the full Section 3 schema; all backend work depends on this being correct.
- `frontend/src/app/admin/layout.tsx` and `frontend/src/app/(portal)/layout.tsx` — the two auth-gated shells defining the portal split.
- `backend/app/services/storage_service.py` — local/S3 storage abstraction that uploads/downloads/versioning all funnel through.
- `ai/ai_core/embeddings.py` — shared PyTorch inference module used by both the notebook and the FastAPI backend.
- `frontend/src/lib/api-client.ts` — the single fetch wrapper handling cookies, CSRF, and 401-refresh-retry for the whole frontend.

## Verification Plan

- After each phase, run the backend (`uvicorn app.main:app --reload`) and frontend (`next dev`) locally and walk through that phase's flow in the browser preview tool.
- Backend: `pytest` for services/permission logic (introduced incrementally, formalized in Phase 6).
- Frontend: Playwright E2E for the critical flows, added in Phase 6.
- Manual DB check via `psql`/Neon SQL console to confirm migrations and seeded roles/permissions after Phase 0/1.
- Before declaring the project "done," run the full flow end-to-end from a clean checkout per the README.

## Immediate next step after approval

Ask the user to create a free Neon project and provide a `DATABASE_URL` (or walk them through Neon signup) before Phase 0 scaffolding begins, since the backend can't boot/migrate without it.
