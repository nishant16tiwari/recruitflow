from sqlalchemy.orm import Session

from app.models.application_history import ApplicationHistory
from app.models.enums import HistoryEventType, Stage


def record_event(
    db: Session,
    *,
    application_id: int,
    event_type: HistoryEventType,
    actor_id: int,
    from_stage: Stage | None = None,
    to_stage: Stage | None = None,
    note: str = "",
) -> ApplicationHistory:
    """
    The ONLY function in the codebase that inserts into application_history.
    WHY centralizing this matters: it guarantees every history row has a
    consistent shape and makes it easy to confirm (by code review alone)
    that there is no update/delete path anywhere - grep the codebase for
    ApplicationHistory and every usage is either this insert or a read.

    IMPORTANT: this does NOT commit. It's meant to be called inside the
    same db transaction as the state change it's recording (e.g. inside
    advance_stage, right before that function's own commit), so the state
    change and its audit record either both succeed or both roll back
    together - never one without the other.
    """
    event = ApplicationHistory(
        application_id=application_id,
        event_type=event_type,
        from_stage=from_stage,
        to_stage=to_stage,
        actor_id=actor_id,
        note=note,
    )
    db.add(event)
    return event
