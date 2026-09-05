"""
Seed data for local development / demos.

WHY this talks to the ORM directly instead of calling the FastAPI routes:
several rows need specific BACKDATED timestamps (applications spread over
the last quarter so the dashboard chart has something to show; one
candidate deliberately stalled >10 days) that the live API deliberately
has no way to set - stage_entered_at and applied_date are always
"now"/server-controlled in normal use, which is correct for the real
app but means a seed script has to go around the API to construct a
realistic-looking history.

Run with:  python seed.py
This WIPES all existing data in the dev database before reseeding, so
never point this at anything but a local/dev database.
"""

import random
from datetime import date, datetime, timedelta, timezone

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.alert_dismissal import AlertDismissal
from app.models.application import Application
from app.models.application_history import ApplicationHistory
from app.models.application_panel import ApplicationPanel
from app.models.enums import HistoryEventType, JobStatus, Stage, UserRole
from app.models.feedback import Feedback
from app.models.interview import Interview, InterviewInterviewer
from app.models.job_opening import JobOpening
from app.models.user import User

random.seed(42)  # deterministic seed data across runs


def wipe_all(db):
    print("Wiping existing data...")
    for model in [
        AlertDismissal,
        Feedback,
        InterviewInterviewer,
        Interview,
        ApplicationHistory,
        ApplicationPanel,
        Application,
        JobOpening,
        User,
    ]:
        db.query(model).delete()
    db.commit()


def make_user(db, email, name, role, password="password123"):
    user = User(email=email, name=name, role=role, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    return user


def make_job(db, title, department, description, status, created_by):
    job = JobOpening(title=title, department=department, description=description, status=status, created_by=created_by)
    db.add(job)
    db.flush()
    return job


def add_history(db, application_id, event_type, actor_id, from_stage=None, to_stage=None, note="", when=None):
    event = ApplicationHistory(
        application_id=application_id,
        event_type=event_type,
        from_stage=from_stage,
        to_stage=to_stage,
        actor_id=actor_id,
        note=note,
    )
    db.add(event)
    db.flush()
    if when is not None:
        event.created_at = when
    return event


def make_application(
    db, job_id, candidate_name, candidate_email, source, current_stage, applied_date, stage_entered_at,
    created_by, previous_stage_before_rejection=None, notes="",
):
    app_ = Application(
        job_id=job_id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        source=source,
        notes=notes,
        applied_date=applied_date,
        current_stage=current_stage,
        stage_entered_at=stage_entered_at,
        previous_stage_before_rejection=previous_stage_before_rejection,
        created_by=created_by,
    )
    db.add(app_)
    db.flush()
    add_history(
        db, app_.id, HistoryEventType.CREATED, created_by, to_stage=Stage.APPLIED,
        note=f"Application created for {candidate_name}", when=datetime.combine(applied_date, datetime.min.time(), tzinfo=timezone.utc),
    )
    return app_


def seed():
    db = SessionLocal()
    try:
        wipe_all(db)

        print("Creating users...")
        recruiter = make_user(db, "Nishant@recruitflow.dev", "Nishant Tiwari", UserRole.RECRUITER)
        recruiter2 = make_user(db, "Shivam@recruitflow.dev", "Shivam Singh", UserRole.RECRUITER)
        interviewer1 = make_user(db, "Hardik.interviewer@recruitflow.dev", "Hardik Pandaya", UserRole.INTERVIEWER)
        interviewer2 = make_user(db, "Rohit.interviewer@recruitflow.dev", "Rohit Sharma", UserRole.INTERVIEWER)
        interviewer3 = make_user(db, "amara.interviewer@recruitflow.dev", "Amara", UserRole.INTERVIEWER)
        interviewers = [interviewer1, interviewer2, interviewer3]

        print("Creating job openings...")
        job_backend = make_job(
            db, "Backend Engineer", "Engineering",
            "Own core services powering the recruitment pipeline. Python/FastAPI experience preferred.",
            JobStatus.OPEN, recruiter.id,
        )
        job_frontend = make_job(
            db, "Frontend Engineer", "Engineering",
            "Build the React interface recruiters use every day.",
            JobStatus.OPEN, recruiter.id,
        )
        job_sales = make_job(
            db, "Sales Executive", "Sales",
            "Drive new business for our mid-market segment.",
            JobStatus.OPEN, recruiter2.id,
        )
        job_support = make_job(
            db, "Customer Support Specialist", "Support",
            "Front-line support for our growing customer base.",
            JobStatus.OPEN, recruiter2.id,
        )
        job_archived = make_job(
            db, "Data Analyst (Paused)", "Engineering",
            "Role paused for this quarter - kept here to demonstrate archived jobs.",
            JobStatus.ARCHIVED, recruiter.id,
        )

        today = date.today()
        now = datetime.now(timezone.utc)
        sources = ["LinkedIn", "Referral", "Website", "Job Board", "Career Fair"]

        candidate_names = [
            "Alex Rivera", "Bianca Torres", "Chidi Obi", "Delia Novak", "Ethan Brooks",
            "Farah Haddad", "Grace Kim", "Hugo Meyer", "Ines Duarte", "Jack Sullivan",
            "Kavya Menon", "Liam O'Connor", "Mei Zhang", "Noah Petrov", "Olga Ivanova",
            "Priya Nair", "Quentin Roy", "Rosa Fernandez", "Sten Larsson", "Tara Osei",
        ]

        applications = []

        # --- Spread applications over the last 13 weeks for the dashboard chart ---
        jobs_cycle = [job_backend, job_frontend, job_sales, job_support]
        for i, name in enumerate(candidate_names):
            weeks_ago = random.randint(0, 12)
            applied = today - timedelta(weeks=weeks_ago, days=random.randint(0, 6))
            job = jobs_cycle[i % len(jobs_cycle)]
            email = name.lower().replace(" ", ".").replace("'", "") + "@example.com"
            source = random.choice(sources)

            # Distribute across stages so the "by stage" breakdown is meaningful
            stage_roll = random.random()
            if stage_roll < 0.25:
                stage = Stage.APPLIED
            elif stage_roll < 0.45:
                stage = Stage.SCREENING
            elif stage_roll < 0.65:
                stage = Stage.INTERVIEW
            elif stage_roll < 0.75:
                stage = Stage.OFFER
            elif stage_roll < 0.85:
                stage = Stage.HIRED
            else:
                stage = Stage.REJECTED

            # stage_entered_at: bias toward RECENT activity (most candidates
            # are actively moving), with a long tail so a realistic handful
            # end up genuinely stalled (>10 days) rather than making most of
            # the seed data trigger alerts, which would make the demo noisy.
            applied_dt = datetime.combine(applied, datetime.min.time(), tzinfo=timezone.utc)
            max_offset = max((now - applied_dt).days, 1)
            days_in_current_stage = min(int(random.expovariate(1 / 4)), max_offset)
            stage_entered = applied_dt + timedelta(days=max_offset - days_in_current_stage)

            prev_stage = Stage.INTERVIEW if stage == Stage.REJECTED and random.random() < 0.5 else None

            app_ = make_application(
                db, job.id, name, email, source, stage, applied, stage_entered, recruiter.id,
                previous_stage_before_rejection=prev_stage,
            )
            applications.append(app_)

            # A plausible stage-change history trail for non-Applied candidates
            if stage != Stage.APPLIED:
                add_history(
                    db, app_.id, HistoryEventType.STAGE_CHANGE, recruiter.id,
                    from_stage=Stage.APPLIED, to_stage=Stage.SCREENING if stage != Stage.SCREENING else stage,
                    when=applied_dt + timedelta(days=1),
                )

            # Assign interviewers + feedback for candidates past Screening
            if stage in (Stage.INTERVIEW, Stage.OFFER, Stage.HIRED):
                panel_interviewer = random.choice(interviewers)
                db.add(ApplicationPanel(application_id=app_.id, interviewer_id=panel_interviewer.id))
                db.flush()
                add_history(
                    db, app_.id, HistoryEventType.INTERVIEWER_ASSIGNED, recruiter.id,
                    note=f"{panel_interviewer.name} added to interview panel", when=stage_entered,
                )
                fb = Feedback(
                    application_id=app_.id, interviewer_id=panel_interviewer.id,
                    content=random.choice([
                        "Strong problem-solving skills, communicated clearly throughout.",
                        "Good culture fit, would like a second technical round.",
                        "Solid fundamentals but light on system design experience.",
                        "Excellent communicator, structured answers well under pressure.",
                    ]),
                )
                db.add(fb)
                db.flush()
                add_history(
                    db, app_.id, HistoryEventType.FEEDBACK, panel_interviewer.id, note=fb.content,
                    when=stage_entered + timedelta(hours=2),
                )

            # Rejection history for rejected candidates
            if stage == Stage.REJECTED:
                add_history(
                    db, app_.id, HistoryEventType.REJECTED, recruiter.id,
                    from_stage=prev_stage or Stage.SCREENING, to_stage=Stage.REJECTED,
                    note="Not moving forward at this time", when=stage_entered,
                )

            # Hire history for hired candidates - within the current month so
            # "Hires This Month" has something real to show
            if stage == Stage.HIRED:
                add_history(
                    db, app_.id, HistoryEventType.STAGE_CHANGE, recruiter.id,
                    from_stage=Stage.OFFER, to_stage=Stage.HIRED,
                    note="Offer accepted!", when=now - timedelta(days=random.randint(0, 5)),
                )

        db.commit()

        # --- One deliberately-stalled candidate, per the spec's requirement
        # that seed data include at least one candidate whose current stage
        # is older than 10 days, so the alert system has something to show
        # immediately after seeding. ---
        stalled = make_application(
            db, job_backend.id, "Wren Castillo", "wren.castillo@example.com", "Referral",
            Stage.SCREENING, today - timedelta(days=18),
            now - timedelta(days=14),
            recruiter.id,
            notes="Waiting on take-home assessment results.",
        )
        add_history(
            db, stalled.id, HistoryEventType.STAGE_CHANGE, recruiter.id,
            from_stage=Stage.APPLIED, to_stage=Stage.SCREENING, when=now - timedelta(days=14),
        )
        db.commit()

        # --- A scheduled interview this week, so "Interviews Scheduled This
        # Week" is non-zero out of the box. ---
        interview_candidates = [a for a in applications if a.current_stage == Stage.INTERVIEW]
        if interview_candidates:
            target = interview_candidates[0]
            interview = Interview(
                application_id=target.id,
                date=today + timedelta(days=1),
                start_time=datetime.strptime("14:00", "%H:%M").time(),
                end_time=datetime.strptime("15:00", "%H:%M").time(),
                interview_type="Technical",
                meeting_link="https://meet.example.com/interview",
                created_by=recruiter.id,
            )
            db.add(interview)
            db.flush()
            # Reuse the interviewer already on this application's panel
            # (assigned earlier in this script) instead of picking a new
            # random one, which could collide with the existing panel row
            # and violate the (application_id, interviewer_id) uniqueness
            # constraint.
            existing_panel_entry = (
                db.query(ApplicationPanel).filter(ApplicationPanel.application_id == target.id).first()
            )
            if existing_panel_entry:
                iv_id = existing_panel_entry.interviewer_id
            else:
                iv_id = random.choice(interviewers).id
                db.add(ApplicationPanel(application_id=target.id, interviewer_id=iv_id))
            db.add(InterviewInterviewer(interview_id=interview.id, interviewer_id=iv_id))
            db.commit()

        # --- An application under the archived job, to demonstrate that
        # archiving a job does NOT delete or hide its applications. ---
        make_application(
            db, job_archived.id, "Owen Blackwood", "owen.blackwood@example.com", "LinkedIn",
            Stage.SCREENING, today - timedelta(days=40), now - timedelta(days=20), recruiter.id,
        )
        db.commit()

        print("\nSeed complete.")
        print(f"  Users: {db.query(User).count()}")
        print(f"  Job openings: {db.query(JobOpening).count()}")
        print(f"  Applications: {db.query(Application).count()}")
        print(f"  History events: {db.query(ApplicationHistory).count()}")
        print(f"  Feedback entries: {db.query(Feedback).count()}")
        print("\nDemo accounts (password: password123):")
        print("  Recruiter:   Nishant@recruitflow.dev")
        print("  Recruiter:   Shivam@recruitflow.dev")
        print("  Interviewer: Hardik.interviewer@recruitflow.dev")
        print("  Interviewer: Rohit.interviewer@recruitflow.dev")
        print("  Interviewer: amara.interviewer@recruitflow.dev")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
