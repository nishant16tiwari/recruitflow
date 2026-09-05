from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.application_panel import ApplicationPanel
from app.models.enums import HistoryEventType, UserRole
from app.models.user import User
from app.services import history_service


def list_panel(db: Session, application_id: int) -> list[ApplicationPanel]:
    return (
        db.query(ApplicationPanel)
        .options(joinedload(ApplicationPanel.interviewer))
        .filter(ApplicationPanel.application_id == application_id)
        .all()
    )


def assign_interviewer(db: Session, application_id: int, interviewer_id: int, actor_id: int) -> ApplicationPanel:
    candidate_user = db.get(User, interviewer_id)
    if not candidate_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # WHY this check exists: the spec explicitly requires that recruiters
    # (or any non-INTERVIEWER role) can never be added to an interview
    # panel. A plain foreign key can't express "must reference a row where
    # role = INTERVIEWER," so this is enforced here in the service layer -
    # the one place ALL panel-assignment requests pass through.
    if candidate_user.role != UserRole.INTERVIEWER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with the INTERVIEWER role can be assigned to an interview panel",
        )

    existing = (
        db.query(ApplicationPanel)
        .filter(
            ApplicationPanel.application_id == application_id,
            ApplicationPanel.interviewer_id == interviewer_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This interviewer is already assigned to this application",
        )

    panel_entry = ApplicationPanel(application_id=application_id, interviewer_id=interviewer_id)
    db.add(panel_entry)
    db.flush()

    history_service.record_event(
        db,
        application_id=application_id,
        event_type=HistoryEventType.INTERVIEWER_ASSIGNED,
        actor_id=actor_id,
        note=f"{candidate_user.name} added to interview panel",
    )

    db.commit()
    db.refresh(panel_entry)
    return panel_entry


def remove_interviewer(db: Session, application_id: int, interviewer_id: int, actor_id: int) -> None:
    panel_entry = (
        db.query(ApplicationPanel)
        .filter(
            ApplicationPanel.application_id == application_id,
            ApplicationPanel.interviewer_id == interviewer_id,
        )
        .first()
    )
    if not panel_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interviewer is not on this panel")

    interviewer = db.get(User, interviewer_id)
    db.delete(panel_entry)

    history_service.record_event(
        db,
        application_id=application_id,
        event_type=HistoryEventType.INTERVIEWER_REMOVED,
        actor_id=actor_id,
        note=f"{interviewer.name if interviewer else 'Interviewer'} removed from interview panel",
    )

    db.commit()


def ensure_assigned(db: Session, application_id: int, interviewer_id: int, actor_id: int) -> None:
    """
    Idempotent version of assign_interviewer used by interview scheduling:
    a recruiter scheduling an interview shouldn't have to make a separate
    "add to panel" call first for an interviewer who isn't on it yet, but
    if they already ARE on the panel this must be a silent no-op rather
    than raising the "already assigned" error assign_interviewer normally
    would. Still enforces the INTERVIEWER-role rule via assign_interviewer.
    """
    already = (
        db.query(ApplicationPanel)
        .filter(
            ApplicationPanel.application_id == application_id,
            ApplicationPanel.interviewer_id == interviewer_id,
        )
        .first()
    )
    if not already:
        assign_interviewer(db, application_id, interviewer_id, actor_id)
