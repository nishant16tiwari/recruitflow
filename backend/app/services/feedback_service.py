from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import is_interviewer_assigned
from app.models.enums import HistoryEventType
from app.models.feedback import Feedback
from app.services import history_service


def submit_feedback(db: Session, application_id: int, interviewer_id: int, content: str) -> Feedback:
    """
    WHY the assignment check happens here, in the service, rather than
    only in the route: this function IS the enforcement boundary. Even if
    a future route or script called this directly, it can't produce
    feedback from an unassigned interviewer, because the check is
    inseparable from the write itself.
    """
    if not is_interviewer_assigned(db, application_id, interviewer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit feedback for applications you are assigned to",
        )

    feedback = Feedback(application_id=application_id, interviewer_id=interviewer_id, content=content)
    db.add(feedback)
    db.flush()

    # Mirrored into the immutable timeline so the application detail page's
    # single chronological view includes feedback alongside stage changes,
    # without needing to merge two separate queries client-side.
    history_service.record_event(
        db,
        application_id=application_id,
        event_type=HistoryEventType.FEEDBACK,
        actor_id=interviewer_id,
        note=content,
    )

    db.commit()
    db.refresh(feedback)
    return feedback


def list_feedback(db: Session, application_id: int) -> list[Feedback]:
    return (
        db.query(Feedback)
        .filter(Feedback.application_id == application_id)
        .order_by(Feedback.created_at.asc())
        .all()
    )
