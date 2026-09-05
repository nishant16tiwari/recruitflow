from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.enums import HistoryEventType, Stage
from app.services import history_service

# The ONLY valid forward transitions. This map is the single source of
# truth for pipeline order - every validation function below is derived
# from it, so there is exactly one place to look if the pipeline order
# ever needs to change.
FORWARD_TRANSITIONS: dict[Stage, Stage] = {
    Stage.APPLIED: Stage.SCREENING,
    Stage.SCREENING: Stage.INTERVIEW,
    Stage.INTERVIEW: Stage.OFFER,
    Stage.OFFER: Stage.HIRED,
}

# Stages from which rejection is allowed. WHY Hired and Rejected are
# excluded (an ambiguity call, documented here and in the README): a Hired
# candidate has completed the pipeline successfully, so "rejecting" them
# is not a meaningful pipeline action (offboarding is a different concern
# outside this system's scope); an already-Rejected candidate must be
# explicitly reinstated first before any other transition applies to them.
REJECTABLE_STAGES = {Stage.APPLIED, Stage.SCREENING, Stage.INTERVIEW, Stage.OFFER}


def touch_stage(application: Application, new_stage: Stage) -> None:
    """
    Centralizes the two fields that must ALWAYS change together whenever
    current_stage changes: the stage itself, and the timestamp stall
    detection and reinstatement both depend on.
    """
    application.current_stage = new_stage
    application.stage_entered_at = datetime.now(timezone.utc)


def check_advance(application: Application, requested_to_stage: Stage | None) -> tuple[bool, Stage | None, str | None]:
    """
    Pure validation - no mutation, no exception, no DB write. Returns
    (is_valid, next_stage_if_valid, error_reason_if_invalid).

    WHY this shape: it's reused by both the single-application /advance
    endpoint (which converts a failure into an HTTPException) and the bulk
    /advance endpoint (which converts a failure into one entry in a
    per-item results list, per the bulk-action requirement that one bad
    candidate must never abort the whole batch).
    """
    current = application.current_stage

    if current == Stage.REJECTED:
        return False, None, "Rejected applications must be reinstated before they can advance."

    if current == Stage.HIRED:
        return False, None, "Hired applications cannot be advanced further."

    next_stage = FORWARD_TRANSITIONS.get(current)
    if next_stage is None:
        return False, None, f"No further stage exists after {current.value}."

    if requested_to_stage is not None and requested_to_stage != next_stage:
        return False, None, (
            f"Invalid stage transition. An application in {current.value} must move to "
            f"{next_stage.value} before {requested_to_stage.value}."
        )

    return True, next_stage, None


def advance_stage(
    db: Session, application: Application, actor_id: int, requested_to_stage: Stage | None = None
) -> Application:
    """
    Applies the transition validated by check_advance, inside one
    transaction that also writes the history event, per the requirement
    that a stage change and its audit record can never end up out of sync.
    """
    is_valid, next_stage, reason = check_advance(application, requested_to_stage)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    old_stage = application.current_stage
    touch_stage(application, next_stage)

    history_service.record_event(
        db,
        application_id=application.id,
        event_type=HistoryEventType.STAGE_CHANGE,
        actor_id=actor_id,
        from_stage=old_stage,
        to_stage=next_stage,
    )

    db.commit()
    db.refresh(application)
    return application


def check_reject(application: Application) -> tuple[bool, str | None]:
    if application.current_stage == Stage.REJECTED:
        return False, "This application is already rejected."
    if application.current_stage == Stage.HIRED:
        return False, "A Hired application cannot be rejected."
    return True, None


def reject_application(db: Session, application: Application, actor_id: int, note: str = "") -> Application:
    is_valid, reason = check_reject(application)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    old_stage = application.current_stage
    # WHY store this BEFORE overwriting current_stage: this is the only
    # place in the system that captures "what stage were they in right
    # before rejection," which reinstate_application depends on entirely.
    application.previous_stage_before_rejection = old_stage
    touch_stage(application, Stage.REJECTED)

    history_service.record_event(
        db,
        application_id=application.id,
        event_type=HistoryEventType.REJECTED,
        actor_id=actor_id,
        from_stage=old_stage,
        to_stage=Stage.REJECTED,
        note=note,
    )

    db.commit()
    db.refresh(application)
    return application


def check_reinstate(application: Application) -> tuple[bool, str | None]:
    if application.current_stage != Stage.REJECTED:
        return False, "Only rejected applications can be reinstated."
    if application.previous_stage_before_rejection is None:
        # Defensive - should never happen if reject_application is the only
        # code path that sets current_stage = REJECTED, but we guard anyway
        # rather than silently defaulting to Applied.
        return False, "Cannot reinstate: no prior stage was recorded for this application."
    return True, None


def reinstate_application(db: Session, application: Application, actor_id: int, note: str = "") -> Application:
    is_valid, reason = check_reinstate(application)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    restored_stage = application.previous_stage_before_rejection
    application.previous_stage_before_rejection = None
    # WHY resetting stage_entered_at to now(), not to whenever they
    # originally entered that stage the first time: reinstatement starts a
    # fresh stall-detection clock for that stage. This is a deliberate
    # interpretation, documented in the README - the alternative (resuming
    # the old clock) would mean a candidate could reappear already stalled,
    # which would be a confusing recruiter experience.
    touch_stage(application, restored_stage)

    history_service.record_event(
        db,
        application_id=application.id,
        event_type=HistoryEventType.REINSTATED,
        actor_id=actor_id,
        from_stage=Stage.REJECTED,
        to_stage=restored_stage,
        note=note,
    )

    db.commit()
    db.refresh(application)
    return application
