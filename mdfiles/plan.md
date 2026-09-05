# Plan

## How did you break the work into sessions?

Three distinct phases, across two different working environments:

1. **The initial build** (one long AI-assisted session): analysis and ambiguity resolution, then database schema, then the backend built one requirement at a time — each one implemented and immediately tested against a real database before moving to the next — then the automated test suite, seed data, and documentation, then the frontend built page by page on top of the now-stable API.
2. **Local environment setup and hardening** (a separate session, on a different machine): getting the existing codebase actually running locally (Postgres, Node, the venv), fixing real bugs that only showed up outside the original build environment (a CORS mismatch from using a LAN IP, modals that didn't scroll), and adding features that weren't in the original 10 requirements but were obviously missing once the app was actually being used (double-booking prevention, interview cancellation, a UI redesign).
3. **Deployment** (a final session): git history, then wiring up three free-tier platforms (Vercel, Render, Neon) and fixing the handful of environment-specific issues that only appear once something is actually deployed (connection string format, SSL requirements, SPA routing on a static host).

## What order did you build in, and why that order?

Backend before frontend, entirely — the frontend has nothing to render until there's a real API to call, and building UI against a moving/undefined API contract would have meant redoing work. Within the backend: authentication and the database schema first, since literally every other feature depends on knowing who's making a request and having somewhere to store the answer. Then the pipeline state machine, since job openings and applications are meaningless without the rules that govern how an application moves. Then interview panels and feedback, which depend on applications already existing. Search, bulk actions, the dashboard, and stalled alerts came last because they're all read-heavy features layered on top of data that needed to exist first — you can't test "search across many applications" before applications can be created and moved through stages.

On the frontend, the same logic: authentication and the app shell (routing, sidebar, protected routes) first, then the highest-traffic page (the applications list, since that's where a recruiter spends most of their time), then the detail page, then the more specialized pages (dashboard, alerts, jobs).

The later local session's ordering was driven by necessity rather than planning: you fix what's actually broken (environment setup, then bugs) before you add anything new, and you don't deploy until the thing you're deploying is stable.

## What did you estimate versus what it actually took?

The original plan assumed a slower, more deliberate cadence — analyze, propose, wait for explicit sign-off, then build one phase, repeat. In practice that would have been slower than it needed to be; moving straight into iterative build-and-test cycles per requirement, and only checking in at natural milestones, got through the same amount of work faster without losing correctness, since each piece was still tested before moving on.

The biggest unplanned time cost wasn't a feature at all — it was the build environment itself. Every shell command started a fresh process, so a background Postgres instance or API server from one command simply wasn't there anymore in the next one. That cost several rounds of "why did this just return nothing" before the fix (start every service and run the actual test in one single command) became routine. It's the kind of thing that's invisible in a plan but real in practice.

On the local machine, environment setup (installing Postgres and Node, fixing a PowerShell execution policy blocking the virtualenv, pointing `DATABASE_URL` at localhost instead of the Docker-only hostname) took real, if unglamorous, time before any actual feature work could resume — normal for moving a project to a new machine, but easy to underestimate.

## What did you cut when you ran short?

Nothing from the original 10 requirements — those are all implemented and tested. What got consciously deferred instead:

- **Frontend bundle code-splitting.** The production JS bundle sits over Vite's 500KB warning threshold, mostly because of the charting library. Not broken, just not optimized — lazy-loading the dashboard route would fix it.
- **A CI pipeline.** Tests exist and pass locally; nothing runs them automatically on push yet.
- **Rate limiting and structured production logging/monitoring.** Reasonable to want before real users touch this, not part of the original spec.
- **Email (or any) notifications for newly-scheduled interviews.** Built, then deliberately cut back out — see `decisions.md`.
- **Public self-service signup.** Never started; accounts are provisioned via the seed script by design, not a scope cut under time pressure.
