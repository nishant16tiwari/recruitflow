# RecruitFlow — Technical & Architecture Documentation

## Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 19 + TypeScript + Vite | Fast dev loop, standard, deploys anywhere static (Vercel/Netlify) |
| Styling | Tailwind CSS v4 | Utility-first, no separate CSS files to keep in sync |
| Server state | TanStack Query v5 | Handles caching, invalidation, loading/error states without a separate global store |
| Routing | React Router v7 | Standard, supports nested layouts + protected routes cleanly |
| Charts | Recharts v3 | Declarative, React-native chart composition |
| Forms | React Hook Form + Zod | Performant uncontrolled forms with schema-based validation |
| Backend | FastAPI (Python) | Async-capable, automatic OpenAPI docs, strong Pydantic validation |
| ORM | SQLAlchemy 2.0 | Explicit, typed, mature migration story via Alembic |
| Migrations | Alembic | Autogenerate from models, reviewed before applying |
| Database | PostgreSQL (Neon) | Native enum types, strong constraint support; Neon provides serverless free-tier hosting |
| Auth | JWT in `HttpOnly` cookie | See "Authentication" below |
| Frontend hosting | Vercel | Free tier, CDN-backed static hosting, SPA rewrite support |
| Backend hosting | Render | Free tier Python web service, auto-deploy from GitHub |

---

## High-level architecture

```
Browser
  | HTTP + credentialed cookie
  v
Vercel (React SPA — static build)
  | HTTPS API requests (withCredentials: true)
  v
Render (FastAPI — Python web service)
  | SQLAlchemy / psycopg2
  v
Neon Tech (PostgreSQL — serverless, free tier)
```

### Within the backend:

```
FastAPI routes  (app/api/routes/)
  |  thin — auth dependency + call into services
  v
Service layer   (app/services/)
  |  ALL business logic and validation lives here
  v
SQLAlchemy models (app/models/) -- Alembic migrations
  v
PostgreSQL (Neon)
```

**Why this layering**: routes handle only HTTP concerns (parsing, status codes, dependency injection for auth). Every business rule — stage transition validity, who can do what, how alerts are computed — lives in `app/services/`, independent of HTTP. This is what let the automated test suite exercise business logic directly and made it possible to reuse the same validation function (e.g. `pipeline_service.check_advance`) in both the single-application endpoint and the bulk-action endpoint without duplicating the rule.

---

## Authentication & Authorization

### Authentication
JWT stored in an `HttpOnly`, `SameSite=Lax` cookie — **not** `localStorage`. An `HttpOnly` cookie is invisible to any JavaScript running on the page, which removes the most common XSS-based token theft vector entirely. The tradeoff is CORS complexity (the frontend must send `withCredentials: true`, and the backend must echo the exact origin rather than `*` — see `app/main.py`'s CORS middleware config), which is wired up correctly and verified in production.

### Authorization — two layers, both server-side
1. **Role-level**: `require_role()` in `app/core/deps.py` is a dependency factory. Each route declares which role(s) may call it (`Depends(require_role(UserRole.RECRUITER))`). This runs before any business logic, so even a hand-crafted `curl`/Postman request gets a 403 regardless of what the frontend would have shown.
2. **Resource-level**: `is_interviewer_assigned()` / `authorize_application_access()` check, on every single request, whether the current interviewer is actually on that specific application's panel — checked fresh against the database, never cached in the JWT or anywhere else. This is why removing an interviewer from a panel takes effect on their *very next* request, with zero propagation delay.

**The frontend never enforces authorization on its own** — role-based UI hiding (e.g. not showing the "Advance" button to an interviewer) is a UX nicety, not a security boundary. The backend is the sole source of truth, confirmed by the test suite deliberately calling restricted endpoints as the wrong role and asserting 403.

---

## Data model

Core entities (see `backend/app/models/` for full definitions):

```
users --< application_panel >-- applications --> job_openings
                                      |
                                      |--< application_history  (append-only)
                                      |--< feedback              (append-only)
                                      |--< interviews --< interview_interviewers
                                      '--< alert_dismissals
```

- **`applications.job_id`** — `ON DELETE RESTRICT`, not `CASCADE`. A job can never be hard-deleted out from under its applications (in practice jobs are only archived, never deleted, but this is a structural safety net).
- **`application_panel`** — many-to-many join table between applications and interviewers. Role correctness (only `INTERVIEWER`-role users) is enforced in the service layer, since a plain foreign key can't express "must reference a row where role = X."
- **`application_history`** — see "Immutable History" below.
- **`alert_dismissals`** — keyed by `(application_id, stage, stage_entered_at)`, not just `application_id`. See "Stalled Alerts" below — this is the whole mechanism that makes dismissal apply to one stall episode rather than forever.

### Indexes
Deliberately placed on fields used in the search/filter/sort/alert queries: `candidate_name`, `candidate_email`, `source`, `current_stage`, `applied_date`, `stage_entered_at`, `updated_at`, plus a composite `(job_id, current_stage)` for the common "applications for job X in stage Y" query. Not indexed everywhere indiscriminately — each index maps to a real query pattern.

---

## Key architectural decisions worth understanding

### The pipeline state machine
`app/services/pipeline_service.py` holds a single dict, `FORWARD_TRANSITIONS`, as the one source of truth for valid stage order. `check_advance()` is a **pure function** — no DB writes, no exceptions — that returns `(is_valid, next_stage, error_reason)`. This shape is what let the same validation logic power both:
- the single-application `/advance` endpoint (which converts a failure into an HTTP 400), and
- the bulk `/bulk/advance` endpoint (which converts a failure into one entry in a per-item results list, so one bad candidate never aborts the batch)

without duplicating the rule in two places.

### Reinstatement
On rejection, the application's current stage is copied into `previous_stage_before_rejection` *before* being overwritten to `Rejected`. Reinstatement reads that field back and clears it. This guarantees "return to exact prior stage" can't silently degrade into "reset to Applied" — the actual prior value is always what's read back, never inferred or defaulted.

### Immutable history
`app/services/history_service.py`'s `record_event()` is the **only** function anywhere in the codebase that inserts into `application_history`. There is no update or delete route for it — not for recruiters, not for admins, not anywhere. If a correction is ever needed, the design requires appending a new event rather than editing an old one. This is enforced structurally (no code path exists to mutate it), not just by a permission check that could be misconfigured — confirmed by a test that inspects the FastAPI route table itself and asserts no PATCH/PUT/DELETE route touches `/history`.

Every service function that changes application state writes its history event inside the **same transaction** as the state change (via `db.flush()` before `db.commit()`), so state and its audit record can never drift apart.

### Stalled alerts — the trickiest design in the system
An alert is "an application whose `stage_entered_at` is more than 10 days old, and whose stage isn't terminal (Hired/Rejected)." Dismissing an alert must not suppress it forever — only for that specific stretch of time in that stage.

The mechanism: `alert_dismissals` rows are keyed by `(application_id, stage, stage_entered_at)`. The active-alerts query is a single `LEFT JOIN` on that exact triple, filtering for `dismissal.id IS NULL`:

```python
db.query(Application)
  .outerjoin(AlertDismissal, and_(
      AlertDismissal.application_id == Application.id,
      AlertDismissal.stage == Application.current_stage,
      AlertDismissal.stage_entered_at == Application.stage_entered_at,
  ))
  .filter(~Application.current_stage.in_(TERMINAL_STAGES),
           Application.stage_entered_at < cutoff,
           AlertDismissal.id.is_(None))
```

Because `stage_entered_at` changes every time the stage changes (advance, reject, or reinstate all touch it), an old dismissal simply stops matching anything the moment the application moves — no expiry logic, no background job, no manual "un-dismiss" bookkeeping required anywhere else in the system.

### CSV export
Generated server-side using Python's `csv.writer` (proper RFC 4180 escaping for commas/quotes/newlines in candidate names) — never hand-built strings, never generated client-side from possibly-stale data.

### Dashboard: "Hires This Month"
Computed by querying `application_history` for `STAGE_CHANGE` events where `to_stage = Hired` within the current calendar month — **not** by counting applications whose `current_stage` happens to currently be Hired. A candidate hired in June and still marked Hired in September must not count as a September hire; only the permanent history record of *when* the transition happened can answer that correctly.

---

## Frontend architecture

```
src/
  api/          One file per backend resource, each exporting TanStack Query hooks
                (useJobs, useApplicationsSearch, useBulkAdvance, etc.)
  components/   Reusable UI: Layout (sidebar), PipelineStepper, StageBadge,
                Toast, ErrorBoundary, modals (NewApplicationModal, JobFormModal,
                ScheduleInterviewModal)
  hooks/        useAuth (login/logout/current-user, backed by TanStack Query cache)
  lib/          api.ts (axios client with withCredentials: true), types.ts (mirrors backend schemas)
  pages/        One component per route
```

**No separate global state store.** All server data lives in TanStack Query's cache; mutations call `queryClient.invalidateQueries()` on the relevant keys after success, so the UI reflects the backend's actual post-mutation state rather than an optimistic guess that could drift from reality. Auth state is just the `['auth', 'me']` query — login/logout directly set or clear that cache entry.

**Route protection**: `ProtectedRoute` redirects to `/login` if there's no authenticated user, and redirects to the correct home page if the user's role doesn't match a route's `requireRole`. This is a UX convenience — the real enforcement is server-side, as covered above.

**Error boundary**: `ErrorBoundary` component wraps the whole app to catch rendering errors and show a friendly fallback instead of a white screen crash.

---

## Deployment Details

### Backend startup sequence (Render)
The `render.yaml` `startCommand` runs in order:
1. `alembic upgrade head` — applies any pending DB migrations against Neon
2. `python seed.py` — seeds demo data (idempotent)
3. `uvicorn app.main:app --host 0.0.0.0 --port $PORT` — starts the API server

### Neon PostgreSQL notes
- Neon is a serverless PostgreSQL that "branches" like Git. The free tier provides one branch with 512MB storage.
- The connection string from Neon must be adapted for SQLAlchemy: replace the `postgres://` scheme with `postgresql+psycopg2://` and append `?sslmode=require`.
- Neon connections can time out after idling; psycopg2's connection pool handles reconnection automatically.

### Render free tier behavior
- Backend sleeps after ~15 minutes of inactivity; first request after wakeup is slow (~30–60 seconds).
- Logs are available in the Render dashboard under the service's "Logs" tab.
- Environment variables are set in Render → Service → Environment tab (not committed to repo).

---

## Security summary

- Passwords: bcrypt via `passlib`, confirmed hashed (never plaintext) in the database
- Session: JWT in `HttpOnly`, `SameSite=Lax` cookie
- CORS: explicit origin allowlist (`CORS_ORIGINS` env var), `allow_credentials=True`
- SQL injection: not applicable — 100% SQLAlchemy ORM/Core, no raw string-interpolated queries anywhere
- Input validation: Pydantic schemas on every endpoint; separate `Create`/`Update`/`Read` shapes so a client can never inject fields like `id` or `role` by including them in a request body
- Secrets: `.env` gitignored, only `.env.example` (no real values) is committed; `JWT_SECRET_KEY` is auto-generated by Render

---

## Testing strategy

68 pytest tests (`backend/tests/`), using a dedicated `recruitflow_test` database that's fully truncated before every single test for isolation. Organized by concern: `test_auth.py`, `test_authorization.py`, `test_pipeline.py`, `test_panel_feedback.py`, `test_search.py`, `test_bulk_and_history.py`, `test_alerts.py`, `test_jobs.py`, `test_dashboard.py`, `test_users.py`.

Notable design choice: tests truncate tables rather than using the more common "wrap in a transaction and roll back" pattern, because the service layer calls `db.commit()` directly in several places (not just `flush()`), which would break a naive rollback-based isolation strategy without rebinding every session to a SAVEPOINT-aware factory. Truncation is slightly slower but works correctly against the application code exactly as written.
