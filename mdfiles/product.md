# RecruitFlow — Product Documentation

## The problem

Hiring teams need a shared, trustworthy record of where every candidate stands. Two failure modes this is meant to prevent:
1. **"Where is this candidate again?"** — ad hoc tracking (spreadsheets, Slack threads, memory) loses state and creates disputes about what happened and when.
2. **Interviewers seeing things they shouldn't.** Recruiters run the process; interviewers should only see and act on candidates they're actually interviewing — not browse the whole company's hiring pipeline.

RecruitFlow solves both with a strict, server-enforced pipeline and a permanent, tamper-proof history.

---

## Who uses it

### Recruiter
Runs the full process. Can:
- Create and manage job openings (create, edit, archive, restore)
- Create and manage candidate applications
- Move candidates through the pipeline, reject, and reinstate
- Assign interviewers to a candidate's panel
- Schedule interviews
- Search, filter, sort, and bulk-act on the candidate list
- Export the pipeline to CSV
- View the recruiting dashboard
- View and dismiss stall alerts

### Interviewer
Restricted view. Can:
- Sign in
- See only applications they're personally assigned to
- View those candidates' details and history
- Leave feedback on candidates they're assigned to
- See their own interview schedule ("My Interviews")

**Interviewers cannot**: change a candidate's stage, reject or reinstate anyone, see unrelated candidates, create or edit job openings, assign other interviewers, or access recruiter-only pages (dashboard, alerts, bulk actions, export). All of this is enforced by the backend, not just hidden in the UI — see `techandartitecture.md`.

---

## The pipeline

Every candidate moves through exactly this sequence, one step at a time:

```
Applied → Screening → Interview → Offer → Hired
```

You cannot skip a stage (e.g. Applied straight to Interview) — the system rejects the attempt and explains what the correct next stage is.

**Rejection** can happen from any active stage (Applied, Screening, Interview, or Offer) — not from Hired (already succeeded) or from an already-Rejected candidate (must be reinstated first).

**Reinstatement** always returns a rejected candidate to the *exact* stage they were in before rejection — never resets them to Applied. A candidate rejected from Interview comes back to Interview, not the beginning of the funnel.

Nothing is ever deleted. A rejected candidate's record, history, and eventual reinstatement are all permanently visible.

---

## Core features, explained

### Job Openings
A job has a title, department, description, and status (Open or Archived). **Archiving a job never touches its applications** — it just hides the job from the default list. This matters because a role can be paused or filled without losing the historical record of who applied to it.

### Applications
Every candidate application belongs to exactly one job opening, and carries: name, email, source (LinkedIn, Referral, Website, etc.), notes, applied date, and current stage.

### Interview Panel & Scheduling
Any number of interviewers can be assigned to a candidate; any interviewer can be on multiple candidates' panels. Only users with the Interviewer role can be assigned — a recruiter can never accidentally end up "interviewing" someone. Scheduling an interview (date, time, interviewer, type, optional link/location) automatically puts that interviewer on the panel if they weren't already there.

### Search, Filter, Sort
The main candidate list supports searching by name/email, filtering by job/stage/source, and sorting by applied date, stage (in pipeline order, not alphabetical), or last updated — all computed on the server, so it stays fast regardless of how many candidates exist.

### Bulk Actions
Select multiple candidates and advance or reject them all at once. If some succeed and some fail (e.g. one is already Hired), **you see exactly which ones failed and why** — a bad candidate in the batch never silently blocks the good ones, and failures are never hidden.

### CSV Export
One click exports every application under an active (non-archived) job opening, with candidate details and current stage, as a real downloadable CSV.

### Dashboard
At a glance: open positions, active applications, interviews scheduled this week, hires this month, a breakdown by job and by stage, and a 13-week trend chart of applications received. "Hires this month" is calculated from the permanent history (not just "who's currently marked Hired"), so it stays accurate even if a hire happened weeks ago and other things have changed since.

### History / Timeline
Every application has a permanent, chronological record: when it was created, every stage change (with who did it), every rejection and reinstatement, every interviewer assignment, and every piece of feedback. This record can never be edited or deleted by anyone — recruiter, interviewer, or otherwise.

### Stalled Alerts
If a candidate sits in the same stage for more than 10 days, an alert appears (with a count badge in the nav). A recruiter can dismiss an alert — but if that same candidate later stalls *again* (in the same stage or a new one), a fresh alert appears. Dismissing an alert is never permanent; it only clears the specific instance of stalling you addressed.

---

## Business rules at a glance

| Rule | Behavior |
|---|---|
| Stage advancement | One step forward at a time only |
| Rejection | Allowed from Applied/Screening/Interview/Offer; not from Hired or already-Rejected |
| Reinstatement | Always returns to the exact pre-rejection stage |
| Archiving a job | Applications are unaffected and remain fully visible |
| Panel assignment | Only Interviewer-role users can be assigned |
| Feedback | Only by an interviewer actually assigned to that candidate |
| "Active" applications (dashboard) | Anything not Hired or Rejected |
| Stall threshold | More than 10 days in the current stage |
| CSV export scope | Every application under a currently-Open job |

---

## Demo accounts

All passwords: `password123`

| Role | Email |
|---|---|
| Recruiter | `recruiter@recruitflow.dev` |
| Recruiter | `recruiter2@recruitflow.dev` |
| Interviewer | `sam.interviewer@recruitflow.dev` |
| Interviewer | `jordan.interviewer@recruitflow.dev` |
| Interviewer | `amara.interviewer@recruitflow.dev` |

> **Note on cold starts**: The backend is hosted on Render's free tier, which sleeps after 15 minutes of inactivity. If the app shows a "Network Error" immediately after opening, wait 30–60 seconds and try again — the backend is waking up. Subsequent requests within the session will be fast.

---

## Deployment

The app is deployed for free across three platforms:

| Service | Platform | URL |
|---|---|---|
| Frontend (React SPA) | Vercel | `https://<your-app>.vercel.app` |
| Backend API (FastAPI) | Render | `https://recruitflow-api.onrender.com` |
| Database (PostgreSQL) | Neon Tech | (connection string, not public) |

Source code: `https://github.com/nishant16tiwari/recruitflow`
