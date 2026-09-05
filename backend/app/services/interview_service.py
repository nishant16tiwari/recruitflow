from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.application import Application
from app.models.enums import HistoryEventType, Stage, UserRole
from app.models.interview import Interview, InterviewInterviewer
from app.models.user import User
from app.schemas.interview import InterviewCreate
from app.services import history_service, panel_service

# WHY these two stages are excluded (documented ambiguity resolution, see
# also README "Business Rules"): a Rejected application isn't actively
# moving through the pipeline, so scheduling a new interview for one
# would be a confusing dead end until it's reinstated; a Hired candidate
# has already finished interviewing by definition. Every other stage
# (including Applied/Screening) is allowed, since recruiters sometimes
# want to line up an interview slot slightly ahead of formally moving the
# candidate into the Interview stage.
NON_SCHEDULABLE_STAGES = {Stage.REJECTED, Stage.HIRED}


def schedule_interview(db: Session, application: Application, data: InterviewCreate, actor_id: int) -> Interview:
    if application.current_stage in NON_SCHEDULABLE_STAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot schedule an interview for an application in {application.current_stage.value} stage",
        )

    interviewer_users = db.query(User).filter(User.id.in_(data.interviewer_ids)).all()
    found_ids = {u.id for u in interviewer_users}
    missing = set(data.interviewer_ids) - found_ids
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown user id(s): {sorted(missing)}")

    non_interviewers = [u.name for u in interviewer_users if u.role != UserRole.INTERVIEWER]
    if non_interviewers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only INTERVIEWER-role users can be scheduled: {', '.join(non_interviewers)} is not an interviewer",
        )

        # Prevent double-booking: check if any selected interviewer already has
    # an overlapping interview slot on the same date. Two ranges overlap
    # when one starts before the other ends, in both directions.
    conflicting = (
        db.query(Interview, User)
        .join(InterviewInterviewer, InterviewInterviewer.interview_id == Interview.id)
        .join(User, User.id == InterviewInterviewer.interviewer_id)
        .filter(
            InterviewInterviewer.interviewer_id.in_(data.interviewer_ids),
            Interview.date == data.date,
            Interview.start_time < data.end_time,
            Interview.end_time > data.start_time,
        )
        .first()
    )
    if conflicting:
        conflicting_interview, conflicting_user = conflicting
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{conflicting_user.name} is already booked on {conflicting_interview.date} "
                f"{conflicting_interview.start_time}-{conflicting_interview.end_time}"
            ),
        )
    
    interview = Interview(
        application_id=application.id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        interview_type=data.interview_type,
        location=data.location,
        meeting_link=data.meeting_link,
        created_by=actor_id,
    )
    db.add(interview)
    db.flush()

    for interviewer_id in data.interviewer_ids:
        db.add(InterviewInterviewer(interview_id=interview.id, interviewer_id=interviewer_id))
        # Auto-adds the interviewer to the application's panel if they
        # aren't already on it - see ensure_assigned's docstring for why.
        panel_service.ensure_assigned(db, application.id, interviewer_id, actor_id)

    history_service.record_event(
        db,
        application_id=application.id,
        event_type=HistoryEventType.INTERVIEW_SCHEDULED,
        actor_id=actor_id,
        note=f"Interview scheduled for {data.date} {data.start_time}-{data.end_time}",
    )

    db.commit()
    db.refresh(interview)
    return interview


def cancel_interview(db: Session, application: Application, interview_id: int, actor_id: int) -> None:
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.application_id == application.id)
        .first()
    )
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    history_service.record_event(
        db,
        application_id=application.id,
        event_type=HistoryEventType.INTERVIEW_CANCELLED,
        actor_id=actor_id,
        note=f"Interview on {interview.date} {interview.start_time}-{interview.end_time} cancelled",
    )

    db.delete(interview)
    db.commit()

def list_interviews_for_application(db: Session, application_id: int) -> list[Interview]:
    return (
        db.query(Interview)
        .options(joinedload(Interview.interviewers))
        .filter(Interview.application_id == application_id)
        .order_by(Interview.date, Interview.start_time)
        .all()
    )


def list_interviews_for_interviewer(db: Session, interviewer_id: int) -> list[Interview]:
    return (
        db.query(Interview)
        .join(InterviewInterviewer, InterviewInterviewer.interview_id == Interview.id)
        .options(joinedload(Interview.interviewers))
        .filter(InterviewInterviewer.interviewer_id == interviewer_id)
        .order_by(Interview.date, Interview.start_time)
        .all()
    )
