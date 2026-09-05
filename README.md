# RecruitFlow

A recruitment pipeline management system: recruiters manage job openings, candidates, interview panels, and a strict hiring pipeline; interviewers get a restricted view limited to applications they're assigned to.

## Overview

RecruitFlow solves a common hiring-team problem: keeping a shared, auditable record of every candidate's progress through a fixed pipeline (`Applied → Screening → Interview → Offer → Hired`), with proper access control between recruiters (who run the process) and interviewers (who only need to see and give feedback on their own assignments) — and an immutable history so "who moved this candidate, and when" is never in dispute.

## Features (mapped to requirements)

| # | Requirement | Where it lives |
|---|---|---|
| 1 | Accounts & roles, server-enforced authorization | `app/core/deps.py`, `app/services/auth_service.py` |
| 2 | Job openings (create/edit/archive/restore, applications survive archiving) | `app/services/job_service.py` |
| 3 | Applications (belong to exactly one job) | `app/services/application_service.py` |
| 4 | Pipeline with strict transitions, rejection, reinstatement | `app/services/pipeline_service.py` |
| 5 | Interview panel + scheduling | `app/services/panel_service.py`, `app/services/interview_service.py` |
| 6 | Search / filter / sort / server-side pagination | `application_service.search_applications` |
| 7 | Bulk actions + CSV export | `app/services/bulk_service.py`, `app/services/export_service.py` |
| 8 | Dashboard | `app/services/dashboard_service.py` |
| 9 | Immutable append-only history | `app/services/history_service.py` (the only writer of `application_history`) |
| 10 | Stalled application alerts | `app/services/alert_service.py` |

## Architecture

```
React + TypeScript + Vite frontend
            ↓  (HTTP + httpOnly cookie auth)
FastAPI backend (routes → services → models)
            ↓
SQLAlchemy ORM + Alembic migrations
            ↓
PostgreSQL
```

**Backend layering**: routes (`app/api/routes/`) handle HTTP concerns and authorization dependencies only; all business logic and validation lives in `app/services/`; `app/models/` are pure SQLAlchemy models with no logic. This keeps authorization and business rules testable independent of HTTP, and keeps route handlers thin.

**Authentication**: JWT stored in an `HttpOnly`, `SameSite=Lax` cookie (not `localStorage`), so it's invisible to any JavaScript running on the page — the standard defense against token theft via XSS. See `app/core/security.py`.

**Authorization**: two layers, both server-side, never trusting the frontend:
1. **Role-level** — `require_role()` in `app/core/deps.py`, a dependency factory used per-route.
2. **Resource-level** — `is_interviewer_assigned()` / `authorize_application_access()`, checked fresh against the database on every request (never cached), so removing an interviewer from a panel takes effect on their very next request.

**History**: `app/services/history_service.py` is the *only* code path in the entire codebase that inserts into `application_history`. There is no update or delete route for it anywhere. If a correction is ever needed, a new event is appended rather than an old one edited.

**Alerts**: see "Business Rules" below for the per-stall-episode dismissal design — the trickiest piece of this system.

## Setup

### With Docker (recommended)

```bash
git clone <repo-url>
cd recruitflow
cp backend/.env.example backend/.env   # edit if needed
docker compose up --build
```

Backend will be available at `http://localhost:8000`, Postgres at `localhost:5432`.

Then, in a separate terminal, run migrations and seed data:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python seed.py
```

### Without Docker (local Postgres)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point DATABASE_URL at your local Postgres
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_URL=http://localhost:8000
npm run dev
```

## Environment Variables

See `backend/.env.example`. Key variables:
- `DATABASE_URL` — Postgres connection string
- `JWT_SECRET_KEY` — **must** be changed to a long random value in production
- `CORS_ORIGINS` — comma-separated list of allowed frontend origins
- `ENVIRONMENT` — `development` or `production` (controls the `Secure` cookie flag)

Never commit a real `.env` file — only `.env.example` is tracked.

## Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description of change"   # generate a new migration
alembic upgrade head                                          # apply migrations
alembic downgrade -1                                           # roll back one migration
```

## Seed Data

```bash
cd backend
python seed.py
```

This **wipes** all data in the target database and recreates a realistic dataset: 5 users, 5 job openings (one archived), 22+ applications spread across the last 13 weeks and every pipeline stage, feedback, a scheduled interview, and at least one genuinely stalled candidate — so the dashboard, charts, and alerts all have real data to show immediately after seeding. Never run this against a production database.

### Demo Accounts (password: `password123`)

| Role | Email |
|---|---|
| Recruiter | `recruiter@recruitflow.dev` |
| Recruiter | `recruiter2@recruitflow.dev` |
| Interviewer | `sam.interviewer@recruitflow.dev` |
| Interviewer | `jordan.interviewer@recruitflow.dev` |
| Interviewer | `amara.interviewer@recruitflow.dev` |

## Running Tests

```bash
cd backend
pytest
```

## API Documentation

With the backend running, interactive Swagger docs are at `http://localhost:8000/docs` (auto-generated by FastAPI from the route/schema definitions — always in sync with the actual code).

## Business Rules

**Pipeline transitions** — exactly one step forward at a time: `Applied → Screening → Interview → Offer → Hired`. The valid-transition map lives in one place (`pipeline_service.FORWARD_TRANSITIONS`) and every jump-ahead attempt is rejected server-side with a specific explanation of what the correct next stage would be.

**Rejection** — allowed from `Applied`, `Screening`, `Interview`, or `Offer`. Not allowed from `Hired` (already successfully completed the pipeline) or from `Rejected` itself (must be reinstated first). *(Documented ambiguity resolution — the spec didn't explicitly exclude Hired.)*

**Reinstatement** — always returns the application to the **exact stage it was in immediately before rejection** (never resets to `Applied`), and starts a fresh 10-day stall clock for that stage.

**Interview scheduling** — cannot be scheduled for a `Rejected` or `Hired` application. Scheduling an interviewer automatically adds them to the application's panel if they weren't already on it. *(Documented ambiguity resolution.)*

**"Active applications"** (dashboard metric) — any application not in `Hired` or `Rejected` (the two terminal states). *(Documented ambiguity resolution.)*

**CSV export "every OPEN application"** — interpreted as every application whose **job opening** has status `OPEN` (not applications whose own stage happens to be non-terminal), since this sits next to the default active-jobs view. *(Documented ambiguity resolution.)*

**Permissions** — recruiters can do everything except submit interview feedback; interviewers can only view/act on applications they're assigned to and can only submit feedback, never change stages. All enforced server-side; see Architecture above.

**History immutability** — enforced structurally: no update/delete route exists for `application_history` anywhere in the codebase, and `history_service.record_event()` is the sole insertion point, always called inside the same transaction as the state change it records.

**Stalled alerts** — an application is stalled when it's been in its current stage (measured from `stage_entered_at`, not creation date) for more than 10 days, and its stage isn't `Hired` or `Rejected`.

Dismissal is scoped to `(application_id, stage, stage_entered_at)` — a specific "stall episode" — not to the application permanently. The moment the application's stage changes, `stage_entered_at` changes too, so the old dismissal no longer matches anything; if the candidate later stalls again (same stage or a new one), a fresh, undismissed alert appears automatically with no expiry logic or background job required. This is implemented as a single `LEFT JOIN ... WHERE dismissal.id IS NULL` query (`alert_service.get_active_alerts`).

## Frontend Architecture

See `frontend/README.md` (added alongside the frontend implementation).

## Troubleshooting

- **`docker compose up` fails to bind port 5432**: you likely have a local Postgres already running on that port. Either stop it, or change the `db` service's port mapping in `docker-compose.yml` (e.g. `"5433:5432"`) and update `DATABASE_URL` in `backend/.env` to match.
- **Frontend requests fail with a CORS error**: make sure `CORS_ORIGINS` in `backend/.env` includes the exact origin the frontend is served from (protocol + host + port), and that `frontend/.env`'s `VITE_API_URL` points at the backend. In production, update `CORS_ORIGINS` to your deployed frontend's real domain.
- **Login succeeds but subsequent requests return 401**: the auth cookie is `HttpOnly` + `SameSite=Lax`; if frontend and backend are deployed on different top-level domains (not just different ports), the browser may still send it for top-level navigation but some setups need `SameSite=None; Secure` instead - only relevant once both are deployed behind HTTPS.
