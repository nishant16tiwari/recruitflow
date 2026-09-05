# AI prompts

The prompts actually used, grouped by what I was trying to achieve, in roughly the order they happened. Most of this comes from the Claude session where the app was actually built; the local-machine session (env setup, bug fixes, redesign, deployment) is summarized at the end from my own work logs, since I didn't keep verbatim prompts for that part.

## Kicking off the build from a full spec

### Prompt
A long master prompt specifying all 10 requirements for the recruitment pipeline system (roles, pipeline rules, interview panels, search/pagination, bulk actions, dashboard, immutable history, stalled alerts), plus an instruction to analyze first and not dump code immediately.

### What you got
A Phase 1 analysis: requirement breakdown, a permissions matrix, the core business rules, a list of genuine ambiguities in the spec with a proposed resolution for each (e.g. what "active application" means, what happens when interview scheduling isn't fully specified), the confirmed tech stack, and a proposed folder structure — no code yet.

### What you corrected
Nothing needed correcting here — I confirmed the plan and told it to start building instead of waiting for sign-off after every phase, since the back-and-forth would have been slower than just building and reviewing in bigger chunks.

## Deciding the stack and starting to build

### Prompt
Actually, I want to deploy this project once it's complete — plan the work accordingly. Also, I want to mention: the tech I recommended isn't compulsory, you can use anything else — but ask me and confirm before using it.Get my confirmation on any important decision or tech choice so I can make sure you're working according to the plan. You can start now.

### What you got
A decision to keep the original React/FastAPI/Postgres stack (justified as genuinely easy to deploy on free platforms), followed by the actual scaffold: Docker Compose, SQLAlchemy models, and an Alembic migration — tested immediately against a real local Postgres instance rather than just written and assumed to work.

### What you corrected
Nothing on my end, but worth noting: the build environment kept losing background processes (Postgres and the API server) between commands, which cost real time until the pattern of "start everything and test it in one single command" was worked out. That's a process fix, not a code fix.

## Building requirement-by-requirement

### Prompt
Mostly continuation — 'continue' — given after reviewing the files being created for each requirement (auth, jobs, applications, pipeline, interview panel, feedback, interview scheduling, search/pagination, bulk actions + CSV, dashboard, stalled alerts) and confirming it matched the plan, before moving on to the next one. When something didn't match the plan, extra input/direction was given to course-correct before continuing."

### What you got
Each requirement built as: schema → service layer (business logic) → route → a real curl-based test against the live database confirming it actually worked, before moving to the next one. Two real bugs surfaced this way:

1. **Sorting by stage** used SQLAlchemy's `case()` with a value-matching dict, which threw a Postgres error (`invalid input value for enum application_stage: "Applied"`). Postgres was storing the enum by its *name* (`APPLIED`) while the dict form sent the *value* (`Applied`) without going through SQLAlchemy's normal per-column enum adaptation.
2. **Stalled-alert detection** used `stage_entered_at <= cutoff`, which flagged an application as stalled at *exactly* 10 days. The spec says "more than 10 days," so this was a real off-by-one — caught by an automated test, not by manual testing.

### What you corrected
1. Rewrote the stage sort as a series of boolean `WHEN` clauses (`case(*whens, else_=99)`) instead of a value-matching dict, which correctly triggers SQLAlchemy's enum adaptation per comparison.
2. Changed the comparison from `<=` to `<` in the alert query, and fixed a flaky test that had been asserting on "exactly 10 days ago" (which becomes *more* than 10 days by the time the assertion actually runs).

## Generating project documentation

### Prompt
"give me handoff.md, design.md, techandartitecture.md, product.md"

### What you got
Four documents covering project status/gaps, the visual design system and reasoning, technical architecture and key decisions, and the product/business rules in plain language.

### What you corrected
Nothing at the time — but these went stale almost immediately once work continued in a separate local session (environment setup, new features, redesign, deployment) that this Claude session had no visibility into. That's less a "correction" and more a lesson: docs generated mid-project need a deliberate re-sync step once work moves to a different tool/session, or they quietly drift from what's actually true.

## Applying a UI reference

### Prompt
A Pinterest link to a signup page design, then (after Pinterest turned out to block automated access) a screenshot upload with: "look at this can we apply it to our ui" — later followed by "apply this ui color combo in whole project."

### What you got
The first pass reskinned the login page: same split-panel/feature-card structure as the reference, but in RecruitFlow's own palette and type instead of copying the source's illustration and brand colors directly. A follow-up pass extended the same dark-panel treatment to the sidebar and to primary buttons app-wide.

### What you corrected
Two things: removed a "Need access? Contact your recruiting admin" line that had been added but wasn't wanted, and — when asked to apply the color combo to "every modal and page" — went back and built a shared modal header component so the three existing modals actually picked up the same dark-header treatment instead of only the sidebar and login page having it.

## Local session: fixes and new features (summarized from work logs, not verbatim prompts)

I didn't keep exact prompt text for this part, but the shape of it: fix the "Network Error" on login (turned out to be opening the app via a LAN IP that didn't match the CORS allowlist, not a real bug), fix modals that didn't scroll on tall content, add a check that stops an interviewer being double-booked, add the ability to cancel a scheduled interview, and — the one worth calling out — build a full SMTP-based email notification system for newly-scheduled interviews, then decide it added more complexity than it was worth and remove it entirely, keeping the in-app "My Interviews" page as the only source of truth.

### What you corrected
The email notification feature itself: built, then fully reverted. See the matching entry in `decisions.md`.

---

## Antigravity (Google DeepMind AI) Session — GitHub Push & Deployment
*5 September 2026. Tool: Antigravity IDE. All prompts below are from this session.*

---

### Prompt 1
> "push the code in this repo https://github.com/nishant16tiwari/recruitflow.git"

#### What you got
The AI checked git status, found no existing git repo, ran `git init -b main`, staged all files, committed, added the remote origin, and attempted to push. Hit a credential/auth hang (Windows Credential Manager was waiting for browser sign-in).

#### What you corrected
The user completed GitHub authentication in the browser. After that, the push went through cleanly.

---

### Prompt 2
> "i have authenticated and authorised git now try to commit and push again"

#### What you got
Re-ran `git push -u origin main` after the credential issue was resolved. Push succeeded — all project files landed on GitHub.

---

### Prompt 3
> "i have built this application with node.js as backend, PostgreSQL as database and frontend and other related stack. I want to deploy the whole app for free. My initial thought process is deploying frontend by Vercel, backend by Render, and I am still unsure about the database. I want to do it for 0 cost, absolutely free. My ultimate goal is to get the live link of the project that can be shared. Study my codebase and help me out."

#### What you got
The AI studied the full codebase (it's actually FastAPI/Python, not Node.js — noted but not an issue for deployment planning). It proposed the stack: **Vercel** (frontend) + **Render** (backend Python web service, free tier) + **Neon Tech** (serverless PostgreSQL, free tier). It outlined all the steps and changes needed to make the app deployable.

---

### Prompt 4
> "yes prepare the codebase"

#### What you got
- Created `render.yaml` at the project root (Render deployment manifest — runtime, build command, start command, env var declarations)
- Created/updated `frontend/vercel.json` with SPA rewrite rules for React Router
- Updated `frontend/.env.example` with `VITE_API_URL` placeholder
- Explained exactly which env vars to set in Render dashboard vs Vercel dashboard

---

### Prompt 5
> "generate a JWT secret key"

#### What you got
A cryptographically secure 64-character random hex string to use as `JWT_SECRET_KEY` in Render's environment variables.

---

### Prompt 6
> "when I tried to login to the app by live Vercel link after all this setup I got network error and then I open the RecruitFlow on Render API and it shows detail not found, then I open Neon Tech PostgreSQL table and it also shows some sort of error. I have pasted all the relevant screenshots, help me out. I am not much of a technical person."

#### What you got
The AI diagnosed three separate problems from the screenshots:
1. **"Network Error" on login** → `CORS_ORIGINS` in Render not matching the Vercel URL
2. **Render showing "detail not found"** → backend was returning a 404 because the `DATABASE_URL` wasn't set or was in the wrong format
3. **Neon table error** → Neon connection string needed `sslmode=require` and the scheme needed changing from `postgres://` to `postgresql+psycopg2://`

Step-by-step fix instructions given for each.

---

### Prompt 7
> "when I clicked on shell it's showing me this" *(screenshot of Render shell being unavailable)*

#### What you got
Explained that Render's **free tier does not include shell access** — that's a paid feature. Alternative: all DB operations (migrations + seed) run automatically via the `startCommand` in `render.yaml` on every deploy. No manual shell needed.

---

### Prompt 8
> "these are the two options in which we have to do" *(screenshot of Render deploy options)*

#### What you got
Guidance on which Render deploy option to pick and how to trigger a manual re-deploy after setting environment variables correctly.

---

### Prompt 9
> *(Pasted Render deploy failure logs — SQLAlchemy engine connection errors)*

#### What you got
Identified the exact cause from the logs: SQLAlchemy `OperationalError` because the Neon connection string was in the wrong format. Provided the exact corrected `DATABASE_URL` string with:
- Scheme changed from `postgres://` to `postgresql+psycopg2://`
- `?sslmode=require` appended

---

### Prompt 10
> "when I schedule an interview and confirm, everything as soon as a new page tried to load it didn't load and this blank white page came in front"

#### What you got
Diagnosed as a React Router + Vercel routing issue: Vercel was returning a 404 for deep URLs (e.g. `/applications/123`) because it didn't know to serve `index.html` for all routes. The fix — the `vercel.json` rewrite rule — was already in the codebase. Confirmed it was committed and instructed a Vercel re-deploy to pick it up. Also added an `ErrorBoundary` component to the frontend to catch any future React render crashes and show a friendly fallback instead of a blank white screen.

---

### Prompt 11
> "@design.md @handoff.md @product.md @techandartitecture.md — these files are taken from Claude Code when it was working on the same project. Now since you are working and the project state has changed a lot since then, update all the files accordingly."

#### What you got
All four documentation files updated to reflect the current real state:
- `handoff.md` — status changed to "deployed", added full deployment architecture, env vars table, known gotchas
- `techandartitecture.md` — Neon/Render/Vercel added to stack, deployment details section, updated library versions
- `product.md` — cold start warning added, deployment summary section added
- `design.md` — ErrorBoundary added to component patterns, library versions updated

Changes committed and pushed to GitHub.

---

### Prompt 12
> "I didn't want these 4 md files to be committed on GitHub, please remove them from GitHub"

#### What you got
Ran `git rm --cached mdfiles/` (removes from git tracking without deleting local files), committed the removal, and pushed. The `mdfiles/` folder now exists only on the local machine — it's not on GitHub.

---


