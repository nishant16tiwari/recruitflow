from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_history import ApplicationHistory
from app.models.enums import HistoryEventType, JobStatus, Stage
from app.models.interview import Interview
from app.models.job_opening import JobOpening
from app.schemas.dashboard import (
    DashboardResponse,
    JobBreakdownItem,
    StageBreakdownItem,
    WeeklyApplicationPoint,
)

# WHY these two stages define "active" (documented ambiguity resolution,
# also in the README): Hired and Rejected are the two terminal states -
# nothing further happens to the application in this pipeline once it
# reaches either one. Every other stage represents a candidate the
# recruiter still needs to act on, which is the practical meaning of
# "active" for a dashboard headline metric.
_TERMINAL_STAGES = {Stage.HIRED, Stage.REJECTED}

# All stages shown in the "by stage" breakdown, in pipeline order,
# INCLUDING Rejected - the master spec's own example explicitly lists
# Rejected alongside the five pipeline stages.
_ALL_STAGES_IN_ORDER = [
    Stage.APPLIED, Stage.SCREENING, Stage.INTERVIEW, Stage.OFFER, Stage.HIRED, Stage.REJECTED,
]


def _week_start(d: date) -> date:
    """Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def get_dashboard(db: Session) -> DashboardResponse:
    today = date.today()
    now = datetime.now(timezone.utc)

    # --- Open Positions ---
    open_positions = db.query(func.count(JobOpening.id)).filter(JobOpening.status == JobStatus.OPEN).scalar()

    # --- Active Applications ---
    active_applications = (
        db.query(func.count(Application.id)).filter(~Application.current_stage.in_(_TERMINAL_STAGES)).scalar()
    )

    # --- Interviews Scheduled This Week (Monday-Sunday containing today) ---
    week_start = _week_start(today)
    week_end = week_start + timedelta(days=6)
    interviews_this_week = (
        db.query(func.count(Interview.id))
        .filter(Interview.date >= week_start, Interview.date <= week_end)
        .scalar()
    )

    # --- Hires This Month (from immutable history, NOT current_stage) ---
    # WHY history and not "count applications currently Hired": a
    # candidate hired in June who is still marked Hired in September
    # must not be counted as a September hire. Only the append-only
    # history row recording WHEN the transition to Hired happened can
    # answer this correctly.
    month_start = today.replace(day=1)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    hires_this_month = (
        db.query(func.count(ApplicationHistory.id))
        .filter(
            ApplicationHistory.event_type == HistoryEventType.STAGE_CHANGE,
            ApplicationHistory.to_stage == Stage.HIRED,
            ApplicationHistory.created_at >= month_start,
            ApplicationHistory.created_at < next_month_start,
        )
        .scalar()
    )

    # --- By Job Opening ---
    job_rows = (
        db.query(JobOpening.id, JobOpening.title, func.count(Application.id))
        .outerjoin(Application, Application.job_id == JobOpening.id)
        .group_by(JobOpening.id, JobOpening.title)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    by_job_opening = [JobBreakdownItem(job_id=jid, job_title=title, count=count) for jid, title, count in job_rows]

    # --- By Stage (every stage always present, even with count 0) ---
    stage_rows = dict(
        db.query(Application.current_stage, func.count(Application.id)).group_by(Application.current_stage).all()
    )
    by_stage = [
        StageBreakdownItem(stage=stage.value, count=stage_rows.get(stage, 0)) for stage in _ALL_STAGES_IN_ORDER
    ]

    # --- Weekly Applications Received, last 13 weeks (~1 quarter) ---
    thirteen_weeks_ago = _week_start(today) - timedelta(weeks=12)
    raw_weekly = (
        db.query(
            func.date_trunc("week", Application.applied_date).label("week"),
            func.count(Application.id),
        )
        .filter(Application.applied_date >= thirteen_weeks_ago)
        .group_by("week")
        .all()
    )
    weekly_counts = {row[0].date(): row[1] for row in raw_weekly}

    # WHY we build the full 13-week list in Python rather than trusting
    # the SQL GROUP BY output directly: a week with zero applications
    # simply never appears as a row in a GROUP BY result, so the chart
    # would silently skip it and misrepresent the data as continuous.
    # Explicitly walking every week and defaulting missing ones to 0 is
    # what "handle weeks with zero applications correctly" means.
    weekly_applications = []
    for i in range(13):
        w_start = thirteen_weeks_ago + timedelta(weeks=i)
        weekly_applications.append(
            WeeklyApplicationPoint(week_start=w_start, count=weekly_counts.get(w_start, 0))
        )

    return DashboardResponse(
        open_positions=open_positions or 0,
        active_applications=active_applications or 0,
        interviews_this_week=interviews_this_week or 0,
        hires_this_month=hires_this_month or 0,
        by_job_opening=by_job_opening,
        by_stage=by_stage,
        weekly_applications=weekly_applications,
    )
