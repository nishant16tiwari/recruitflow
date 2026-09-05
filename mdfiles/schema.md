# Schema

## Table by table

**users**
`id` (PK), `email` (unique, indexed), `password_hash`, `name`, `role` (enum: `RECRUITER` / `INTERVIEWER`, indexed), `created_at`.

**job_openings**
`id` (PK), `title`, `department` (indexed), `description` (text), `status` (enum: `OPEN` / `ARCHIVED`, indexed), `created_by` (FK → users), `created_at`, `updated_at`.

**applications**
`id` (PK), `job_id` (FK → job_openings, `ON DELETE RESTRICT`, indexed), `candidate_name` (indexed), `candidate_email` (indexed), `source` (indexed), `notes` (text), `applied_date` (date, indexed), `current_stage` (enum: Applied/Screening/Interview/Offer/Hired/Rejected, indexed), `stage_entered_at` (timestamp, indexed), `previous_stage_before_rejection` (enum, nullable — only set while `current_stage` is Rejected), `created_by` (FK → users), `created_at`, `updated_at` (indexed). Plus a composite index on `(job_id, current_stage)` for the "applications for this job, in this stage" query used by both the job detail view and the dashboard breakdown.

**application_panel**
`id` (PK), `application_id` (FK → applications, `ON DELETE CASCADE`, indexed), `interviewer_id` (FK → users, indexed), `assigned_at`. Unique on `(application_id, interviewer_id)`.

**interviews**
`id` (PK), `application_id` (FK → applications, `ON DELETE CASCADE`, indexed), `date` (indexed), `start_time`, `end_time`, `interview_type`, `location` (nullable), `meeting_link` (nullable), `created_by` (FK → users), `created_at`.

**interview_interviewers**
`id` (PK), `interview_id` (FK → interviews, `ON DELETE CASCADE`, indexed), `interviewer_id` (FK → users, indexed). A pure join table.

**application_history**
`id` (PK), `application_id` (FK → applications, `ON DELETE CASCADE`, indexed), `event_type` (enum: CREATED / STAGE_CHANGE / REJECTED / REINSTATED / FEEDBACK / INTERVIEW_SCHEDULED / INTERVIEWER_ASSIGNED / INTERVIEWER_REMOVED), `from_stage` (enum, nullable), `to_stage` (enum, nullable), `actor_id` (FK → users), `note` (text), `created_at` (indexed). Append-only — no code path updates or deletes a row here.

**feedback**
`id` (PK), `application_id` (FK → applications, `ON DELETE CASCADE`, indexed), `interviewer_id` (FK → users, indexed), `content` (text), `created_at`. Also append-only.

**alert_dismissals**
`id` (PK), `application_id` (FK → applications, `ON DELETE CASCADE`, indexed), `stage` (enum), `stage_entered_at` (timestamp), `dismissed_by` (FK → users), `dismissed_at`. Unique on `(application_id, stage, stage_entered_at)` — this triple is what makes a dismissal apply to one specific stretch of time in one stage, not to the application forever.

## Relationships

- `users` → `job_openings` (via `created_by`): one-to-many.
- `users` → `applications` (via `created_by`): one-to-many.
- `job_openings` → `applications`: one-to-many. From the application's side this is enforced as belonging to *exactly one* job — a `NOT NULL` foreign key, never a nullable or multi-valued reference.
- `applications` ↔ `users` (interviewers), via `application_panel`: many-to-many. Any number of interviewers per application, any number of applications per interviewer.
- `interviews` ↔ `users` (interviewers), via `interview_interviewers`: many-to-many, same shape as above but scoped to a single scheduled interview rather than the whole application.
- `applications` → `interviews`: one-to-many.
- `applications` → `application_history`: one-to-many.
- `applications` → `feedback`: one-to-many.
- `applications` → `alert_dismissals`: one-to-many.

## Which constraints are enforced by the database, and which by application code?

**Database-enforced:** every foreign key relationship listed above, including the `ON DELETE` behavior (`RESTRICT` on `job_openings → applications` so a job can never be deleted out from under its applications; `CASCADE` everywhere else so a deleted application cleans up its own panel/history/feedback/interviews); the `UNIQUE` constraints (`users.email`, the `application_panel` and `alert_dismissals` composite keys); `NOT NULL` on every required column; and Postgres native enum types for role, job status, application stage, and history event type — these reject an invalid value at the database layer, not just in a Pydantic schema.

**Application-enforced, deliberately:**
- *Only `INTERVIEWER`-role users can be added to a panel or an interview.* A plain foreign key can't express "must reference a row where `role = X`" portably in SQL — this is checked in the service layer before every insert into `application_panel` or `interview_interviewers`.
- *Pipeline stage transitions.* Whether `Screening → Offer` is a legal move isn't a structural fact about the row, it's a business rule about sequencing that also has to account for rejection and reinstatement as separate paths — this lives in one function (`pipeline_service.check_advance`) rather than a database constraint.
- *History is append-only.* Enforced by the *absence* of any update or delete route or function anywhere in the codebase — not by a database trigger or a `REVOKE` on the table. This is a real gap if I were hardening this further: a `REVOKE UPDATE, DELETE` grant (or a trigger that rejects them) would make this true even against a direct database connection, not just through the API.
- *Feedback only from an interviewer actually assigned to that application.* Checked against the `application_panel` table at submission time in the service layer, not expressible as a static constraint since it depends on a separate table's current contents.

The line was drawn there because the database is good at enforcing *structural* facts (this row must reference a valid user; this pair must be unique) but not *business logic* that depends on role values, sequencing, or the current contents of a related table — that logic lives in one well-tested Python function per rule instead, which is also easier to give a precise, human-readable error message from.

## What did you deliberately denormalise?

- `applications.stage_entered_at` duplicates information that could, in principle, be derived from the most recent `STAGE_CHANGE`/`REJECTED`/`REINSTATED` row in `application_history` for that application. It's stored directly on the application row instead, because the stalled-alerts query and the "sort by last updated" search both run on nearly every page load, and deriving this from history would mean a correlated subquery per row instead of a plain indexed column read.
- `previous_stage_before_rejection` is the same trade: technically derivable by looking back through history for the stage before the rejection event, but stored directly so reinstatement is a simple column read instead of a lookback query.

Both of these are updated in the *same transaction* as the history event that would otherwise be the source of truth, so they can't drift out of sync with it. Everything else that could be computed at read time — a job's application count, the dashboard's breakdowns, the weekly chart — deliberately isn't stored anywhere; it's computed fresh with a `COUNT`/`GROUP BY` each time, because those aren't read nearly as often per-row as the two fields above.

## What would break first at 100x the data?

Roughly: from the seed size (~20 applications) to ~2,000+.

- **Candidate search.** Name/email search uses `ILIKE '%term%'`, which a normal B-tree index can't accelerate for a leading wildcard. At 100x rows this would start showing up as real latency. The fix is a Postgres trigram (`pg_trgm`) index on those two columns, not a schema change.
- **CSV export.** It currently builds the entire CSV in memory (`io.StringIO`) before returning it. Fine at a few thousand rows; at a much larger export this should become a genuine streaming response instead of buffering the whole file server-side first.
- **The alerts badge polling.** The query itself scales fine (it's already indexed on the columns it filters on), but every open recruiter tab currently re-polls it every 60 seconds regardless of whether anything changed. At high recruiter counts, that polling pattern — not the query — is the first thing worth replacing with push-based invalidation.
- **The dashboard.** The aggregate queries (by-job, by-stage, weekly chart) are all indexed `GROUP BY`s and would hold up fine on data volume alone; the more likely pressure point is many recruiters loading the dashboard at once, which a short server-side cache would absorb more cheaply than adding more indexes.
