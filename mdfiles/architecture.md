# Architecture

## What are the moving pieces, and how do they talk to each other?

Four pieces:

1. **React frontend** (TypeScript, Vite, Tailwind) — the only thing the browser ever loads. It never talks to the database directly; every piece of data comes from the API.
2. **FastAPI backend** — a single Python service exposing a REST API. Internally it's layered: routes handle HTTP concerns and check who's allowed to call them, service modules hold all the actual business logic and validation, and SQLAlchemy models describe the database tables. Routes are deliberately thin — almost nothing interesting happens in a route handler itself.
3. **PostgreSQL** — the single source of truth for everything: users, jobs, applications, panel assignments, interviews, history, feedback, and alert dismissals.
4. **Alembic migrations** — not a running piece, but the mechanism that keeps the database schema and the SQLAlchemy models in sync as the schema evolves.

The frontend and backend talk over plain HTTPS/JSON, with one important detail: authentication is a JWT stored in an `HttpOnly` cookie, not a bearer token the frontend handles directly. That means the browser sends the cookie automatically on every request (once CORS is configured to allow credentials), and the frontend code never actually touches the token itself.

## Where does each piece run?

- Frontend: built as a static site (`vite build`) and served from Vercel.
- Backend: a single always-on (well — free-tier, so it sleeps after inactivity) web service on Render, running the FastAPI app under Uvicorn.
- Database: a managed Postgres instance on Neon, reached over a normal Postgres connection with SSL required.

Locally, the same three pieces run as: Vite's dev server, Uvicorn with `--reload`, and either a local Postgres install or the Postgres container from `docker-compose.yml`.

## What is the request path for one representative user action, end to end?

**Recruiter advances a candidate to the next pipeline stage:**

1. Browser: recruiter clicks "Advance to next stage" on the application detail page. A TanStack Query mutation fires `POST /applications/{id}/advance` with the auth cookie attached automatically.
2. FastAPI route: the `require_recruiter` dependency runs first and checks the JWT in the cookie, loads the real user row from the database, and confirms their role is `RECRUITER`. If not, this stops here with a 403 and nothing else executes.
3. Service layer (`pipeline_service.py`): loads the application, checks its current stage against the one hard-coded map of valid forward transitions, and either rejects the request with a specific reason (e.g. "Hired applications cannot be advanced further") or computes the correct next stage.
4. If valid: the application's `current_stage` and `stage_entered_at` are updated, and — in the same database transaction — a new row is appended to `application_history` recording the old stage, new stage, and who made the change.
5. Both writes commit together. The updated application is serialized back through a Pydantic schema and returned as JSON.
6. Frontend: the mutation's `onSuccess` handler invalidates the relevant cached queries (this application, the dashboard, the alerts list), so every part of the UI that depends on this application's state refetches and reflects the change — no manual state syncing anywhere.

## What did you decide *not* to build, and why?

- **Public self-service signup.** Accounts are created via a seed script / admin action, not a signup form. A recruiting tool with open registration would let anyone assign themselves a role, which defeats the point of having roles at all.
- **A general-purpose calendar/scheduling system.** Interview scheduling only stores what the dashboard's "interviews this week" metric and the interview panel actually need — date, time, interviewer(s), type, optional link. No recurring interviews, no calendar UI, no conflict detection beyond what was explicitly needed.
- **Real-time updates (websockets/polling for live collaboration).** Two recruiters editing the same application at the same moment is a real but rare scenario for a small team tool; it wasn't worth the complexity versus just refetching on navigation and on a timer for the alerts badge.
- **A CI pipeline, rate limiting, and structured production logging.** All genuinely worth having before this is used for real hiring decisions, but none of them were part of the original 10 requirements, and adding them speculatively would have been effort spent on infrastructure instead of the actual feature set that was asked for.
- **Database-level enforcement of every business rule.** Some rules (only interviewers can be assigned to a panel, feedback only from an assigned interviewer, no editing history) are enforced in the service layer instead of with database triggers or check constraints. See `schema.md` for why.
