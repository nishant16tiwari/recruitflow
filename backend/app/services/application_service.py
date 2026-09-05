from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.core.deps import is_interviewer_assigned
from app.models.application import Application
from app.models.application_panel import ApplicationPanel
from app.models.enums import HistoryEventType, JobStatus, Stage, UserRole
from app.models.job_opening import JobOpening
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services import history_service


def get_application_or_404(db: Session, application_id: int) -> Application:
    app_ = db.get(Application, application_id)
    if not app_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return app_


def authorize_application_access(db: Session, application: Application, user: User) -> None:
    """
    Resource-level authorization, called by every route that reads or acts
    on a specific application. Recruiters can access any application.
    Interviewers can access ONLY applications they are on the panel for -
    checked fresh against the database on every request, never cached or
    inferred from the JWT, so removing an interviewer from a panel takes
    effect immediately on their very next request.
    """
    if user.role == UserRole.RECRUITER:
        return
    if user.role == UserRole.INTERVIEWER and is_interviewer_assigned(db, application.id, user.id):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to access this application",
    )


def create_application(db: Session, data: ApplicationCreate, created_by: int) -> Application:
    job = db.get(JobOpening, data.job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opening not found")
    if job.status != JobStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add a new application to an archived job opening",
        )

    app_ = Application(
        job_id=data.job_id,
        candidate_name=data.candidate_name,
        candidate_email=data.candidate_email,
        source=data.source,
        notes=data.notes,
        applied_date=data.applied_date or date.today(),
        current_stage=Stage.APPLIED,
        created_by=created_by,
    )
    db.add(app_)
    db.flush()  # assigns app_.id without committing yet

    history_service.record_event(
        db,
        application_id=app_.id,
        event_type=HistoryEventType.CREATED,
        actor_id=created_by,
        to_stage=Stage.APPLIED,
        note=f"Application created for {data.candidate_name}",
    )

    db.commit()
    db.refresh(app_)
    return app_


def update_application(db: Session, application: Application, data: ApplicationUpdate) -> Application:
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


def list_applications_for_job(db: Session, job_id: int) -> list[Application]:
    return (
        db.query(Application)
        .filter(Application.job_id == job_id)
        .order_by(Application.created_at.desc())
        .all()
    )


def list_applications_for_interviewer(db: Session, interviewer_id: int) -> list[Application]:
    """
    Powers the "My Interviews / My Applications" view. Joins through the
    panel table so an interviewer only ever sees applications they are
    actually assigned to - this is the query-level equivalent of the same
    rule enforced in authorize_application_access for single-record access.
    """
    return (
        db.query(Application)
        .join(ApplicationPanel, ApplicationPanel.application_id == Application.id)
        .filter(ApplicationPanel.interviewer_id == interviewer_id)
        .order_by(Application.updated_at.desc())
        .all()
    )


# Fixed pipeline order used for "sort by stage" - see search_applications.
# WHY not alphabetical: alphabetical order (Applied, Hired, Interview,
# Offer, Rejected, Screening) is meaningless to a recruiter scanning a
# table; this ordering matches the actual funnel so ascending genuinely
# means "earliest in the pipeline first."
_STAGE_SORT_ORDER = {
    Stage.APPLIED: 1,
    Stage.SCREENING: 2,
    Stage.INTERVIEW: 3,
    Stage.OFFER: 4,
    Stage.HIRED: 5,
    Stage.REJECTED: 6,
}


def search_applications(
    db: Session,
    user: User,
    *,
    search: str | None,
    job_id: int | None,
    stage: Stage | None,
    source: str | None,
    sort_by: str,
    sort_order: str,
    page: int,
    page_size: int,
) -> tuple[list[Application], int]:
    """
    The single query-construction point for Requirement 6. Everything -
    authorization scoping, search, filters, sorting, pagination - happens
    as SQL clauses on one query, so the database (not Python) does the
    filtering/sorting/counting. This is what makes it safe against large
    datasets: we never pull more than one page of rows into memory.

    Returns (page_of_results, total_matching_count).
    """
    query = db.query(Application)

    # --- Authorization scoping (always applied first, never optional) ---
    if user.role == UserRole.INTERVIEWER:
        query = query.join(ApplicationPanel, ApplicationPanel.application_id == Application.id).filter(
            ApplicationPanel.interviewer_id == user.id
        )
    # Recruiters see every application across every opening (including
    # ones under archived jobs - archiving hides the JOB, not applications).

    # --- Search: name OR email, case-insensitive substring match ---
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Application.candidate_name.ilike(like_pattern),
                Application.candidate_email.ilike(like_pattern),
            )
        )

    # --- Filters ---
    if job_id is not None:
        query = query.filter(Application.job_id == job_id)
    if stage is not None:
        query = query.filter(Application.current_stage == stage)
    if source is not None:
        query = query.filter(Application.source == source)

    # --- Total count BEFORE pagination (for total/total_pages in response) ---
    total = query.with_entities(func.count(Application.id)).scalar()

    # --- Sorting ---
    descending = sort_order == "desc"
    if sort_by == "applied_date":
        order_col = Application.applied_date
        query = query.order_by(order_col.desc() if descending else order_col.asc())
    elif sort_by == "last_updated":
        order_col = Application.updated_at
        query = query.order_by(order_col.desc() if descending else order_col.asc())
    elif sort_by == "stage":
        whens = [(Application.current_stage == stage, order) for stage, order in _STAGE_SORT_ORDER.items()]
        stage_case = case(*whens, else_=99)
        query = query.order_by(stage_case.desc() if descending else stage_case.asc())
    else:
        query = query.order_by(Application.updated_at.desc())

    # --- Pagination: server-side offset/limit, never load-all-then-slice ---
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return items, total
