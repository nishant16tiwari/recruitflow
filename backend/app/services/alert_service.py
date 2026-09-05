from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.alert_dismissal import AlertDismissal
from app.models.application import Application
from app.models.enums import Stage
from app.models.job_opening import JobOpening
from app.schemas.alert import AlertItem

# WHY 10 days, and why current_stage exclusions: per the master spec, a
# stall is measured from stage_entered_at, and Hired/Rejected are
# terminal states where "stalling" has no meaning - a Hired candidate
# sitting in the Hired stage for 30 days isn't a problem to alert on.
STALL_THRESHOLD_DAYS = 10
_TERMINAL_STAGES = {Stage.HIRED, Stage.REJECTED}


def get_active_alerts(db: Session) -> list[AlertItem]:
    """
    The core query implementing both stall detection AND the
    per-stall-episode dismissal rule in one pass.

    WHY the join condition matches on (application_id, stage,
    stage_entered_at) rather than just application_id: this is the exact
    mechanism that makes a dismissal apply ONLY to the specific stretch of
    time being dismissed. If the application has since moved to a new
    stage (new stage_entered_at), no AlertDismissal row will match this
    join's ON clause even though a dismissal exists for this application -
    it was for a different episode - so the LEFT JOIN produces NULL and
    the application appears in results again, i.e. the alert reappears
    with zero extra bookkeeping needed anywhere else in the system.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=STALL_THRESHOLD_DAYS)

    rows = (
        db.query(Application, JobOpening.title)
        .join(JobOpening, JobOpening.id == Application.job_id)
        .outerjoin(
            AlertDismissal,
            and_(
                AlertDismissal.application_id == Application.id,
                AlertDismissal.stage == Application.current_stage,
                AlertDismissal.stage_entered_at == Application.stage_entered_at,
            ),
        )
        .filter(
            ~Application.current_stage.in_(_TERMINAL_STAGES),
            Application.stage_entered_at < cutoff,
            AlertDismissal.id.is_(None),
        )
        .order_by(Application.stage_entered_at.asc())
        .all()
    )

    alerts = []
    for application, job_title in rows:
        stage_entered_at = application.stage_entered_at
        if stage_entered_at.tzinfo is None:
            stage_entered_at = stage_entered_at.replace(tzinfo=timezone.utc)
        days_in_stage = (now - stage_entered_at).days
        alerts.append(
            AlertItem(
                application_id=application.id,
                candidate_name=application.candidate_name,
                job_id=application.job_id,
                job_title=job_title,
                current_stage=application.current_stage,
                stage_entered_at=application.stage_entered_at,
                days_in_stage=days_in_stage,
            )
        )
    return alerts


def dismiss_alert(db: Session, application_id: int, dismissed_by: int) -> None:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=STALL_THRESHOLD_DAYS)
    stage_entered_at = application.stage_entered_at
    if stage_entered_at.tzinfo is None:
        stage_entered_at_check = stage_entered_at.replace(tzinfo=timezone.utc)
    else:
        stage_entered_at_check = stage_entered_at

    is_currently_stalled = (
        application.current_stage not in _TERMINAL_STAGES and stage_entered_at_check < cutoff
    )
    if not is_currently_stalled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This application does not currently have an active stall alert",
        )

    existing = (
        db.query(AlertDismissal)
        .filter(
            AlertDismissal.application_id == application_id,
            AlertDismissal.stage == application.current_stage,
            AlertDismissal.stage_entered_at == application.stage_entered_at,
        )
        .first()
    )
    if existing:
        # Idempotent: dismissing an already-dismissed episode is a no-op,
        # not an error - a recruiter double-clicking "dismiss" shouldn't
        # see a failure.
        return

    dismissal = AlertDismissal(
        application_id=application_id,
        stage=application.current_stage,
        stage_entered_at=application.stage_entered_at,
        dismissed_by=dismissed_by,
    )
    db.add(dismissal)
    db.commit()
