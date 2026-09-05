# Decisions

## Decision 1

- **Chose:** Store the auth token as a JWT inside an `HttpOnly`, `SameSite=Lax` cookie.
- **Rejected:** Storing the JWT in `localStorage` and attaching it as an `Authorization` header from the frontend.
- **Why:** `localStorage` is readable by any JavaScript running on the page, so a single XSS bug anywhere in the frontend (or in a compromised dependency) could steal the token outright. An `HttpOnly` cookie is invisible to JavaScript entirely, which removes that attack surface. The tradeoff is CORS complexity — the frontend has to send `withCredentials: true` and the backend has to echo back the exact origin instead of `*` — but that's a one-time setup cost, not an ongoing risk.

## Decision 2

- **Chose:** Reinstating a rejected candidate resets their stall-detection clock (`stage_entered_at` is set to the moment of reinstatement).
- **Rejected:** Resuming the old elapsed time — i.e. if they'd already spent 8 days in Interview before being rejected, they'd reappear already 8 days into a new 10-day countdown.
- **Why:** The spec didn't say either way. Resuming the old clock means a recruiter could reinstate someone and have them show up on the stalled-alerts list almost immediately, which reads as confusing and unearned — from the recruiter's perspective, they just took an action, they shouldn't be immediately warned about inaction. A fresh clock matches how a recruiter actually thinks about it: reinstatement is a fresh start for that stage.

## Decision 3

- **Chose:** Rejection is allowed from Applied, Screening, Interview, or Offer — not from Hired, and not from an application that's already Rejected.
- **Rejected:** Allowing rejection from any stage including Hired, or treating "already rejected" as a no-op instead of a hard error.
- **Why:** The spec said rejection is allowed "from any stage" but only ever gave examples from the four active stages. A Hired candidate has already completed the pipeline successfully — "rejecting" them at that point isn't a pipeline action, it's an offboarding decision that belongs to a different part of an HR system, if it exists at all. An already-rejected application returning a clear error (rather than silently doing nothing) matches the same "duplicate-request protection" pattern used for stage advancement.

## Decision 4

- **Chose:** SMTP-based email notifications when an interview is scheduled — designed, built, then removed entirely.
- **Rejected (in the end):** Any notification system at all; the in-app "My Interviews" page is the sole source of truth for an interviewer's schedule.
- **Why:** The gap was real — an interviewer has no way to know they've been scheduled unless they happen to open the app. Email notifications were the obvious fix and got built (SMTP client, Gmail App Password setup, a notification service that fired on successful scheduling). But it added a whole new category of things that could fail silently in production (wrong credentials, provider rate limits, emails landing in spam) for a feature that wasn't part of the original 10 requirements, and the app was already usable as long as interviewers got in the habit of checking their schedule. Simpler won.
- **Later reversed:** This is the reversal itself — the decision to build it came first; the decision to rip it back out came after weighing the actual maintenance cost against how much it was really needed.

## Decision 5

- **Chose:** Vercel (frontend) + Render (backend) + Neon (Postgres), all free tier.
- **Rejected:** Self-hosting everything with Docker Compose on a single VPS.
- **Why:** The project already had a working `docker-compose.yml`, so self-hosting was genuinely on the table. But the three managed platforms cost nothing to start, deploy straight from a GitHub push with no server to patch or monitor, and each one is good at exactly the one job it's doing (static hosting, Python web services, Postgres). The real cost is the free-tier cold start on Render (the API sleeps after 15 minutes of inactivity, so the first request after a break takes 30–60 seconds) — an accepted tradeoff for a demo/portfolio project, not something that would be acceptable for a paying customer's production app.
