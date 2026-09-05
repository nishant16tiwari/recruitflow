from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Literal

from app.core.deps import get_current_user, require_interviewer, require_recruiter
from app.db.session import get_db
from app.models.user import User
from app.models.application_history import ApplicationHistory
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.schemas.bulk import BulkActionRequest, BulkActionResponse
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.schemas.history import HistoryEventRead
from app.schemas.interview import InterviewCreate, InterviewRead
from app.schemas.pagination import PaginatedResponse
from app.schemas.panel import PanelAssignRequest, PanelMemberRead
from app.schemas.pipeline import AdvanceRequest, ReinstateRequest, RejectRequest
from app.services import application_service, feedback_service, interview_service, panel_service, pipeline_service
from app.services import bulk_service, export_service
from app.models.enums import Stage

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    return application_service.create_application(db, data, created_by=current_user.id)


@router.get("", response_model=PaginatedResponse[ApplicationRead])
def search_applications(
    search: str | None = Query(default=None, description="Matches candidate name or email"),
    job_id: int | None = Query(default=None),
    stage: Stage | None = Query(default=None),
    source: str | None = Query(default=None),
    sort_by: Literal["applied_date", "stage", "last_updated"] = Query(default="last_updated"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requirement 6 - global candidate search. Recruiters see every
    application they're authorized to see (all of them); interviewers see
    only applications they're assigned to. Everything - search, filters,
    sorting, pagination - is pushed down into the SQL query in
    application_service.search_applications; nothing is loaded into
    Python and filtered/sliced here.
    """
    items, total = application_service.search_applications(
        db,
        current_user,
        search=search,
        job_id=job_id,
        stage=stage,
        source=source,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(items=items, page=page, page_size=page_size, total=total, total_pages=total_pages)


@router.get("/my", response_model=list[ApplicationRead])
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    """
    WHY this route MUST be declared before GET /{application_id}: Starlette
    matches routes in registration order, and "/my" would otherwise be
    swallowed by the "/{application_id}" pattern (causing a 422 trying to
    parse "my" as an int) before ever reaching this handler.
    """
    return application_service.list_applications_for_interviewer(db, current_user.id)


# ---------------------------------------------------------------------------
# Bulk actions and CSV export - also static paths, also registered before
# the "/{application_id}" catch-all for the same reason as "/my" above.
# ---------------------------------------------------------------------------


@router.post("/bulk/advance", response_model=BulkActionResponse)
def bulk_advance(
    data: BulkActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    results = bulk_service.bulk_advance(db, data.application_ids, actor_id=current_user.id)
    return BulkActionResponse(results=results)


@router.post("/bulk/reject", response_model=BulkActionResponse)
def bulk_reject(
    data: BulkActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    results = bulk_service.bulk_reject(db, data.application_ids, actor_id=current_user.id)
    return BulkActionResponse(results=results)


@router.get("/export")
def export_pipeline_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    csv_content = export_service.generate_pipeline_csv(db)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pipeline_export.csv"},
    )


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_ = application_service.get_application_or_404(db, application_id)
    application_service.authorize_application_access(db, app_, current_user)
    return app_


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    data: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    app_ = application_service.get_application_or_404(db, application_id)
    return application_service.update_application(db, app_, data)


@router.post("/{application_id}/advance", response_model=ApplicationRead)
def advance_application(
    application_id: int,
    data: AdvanceRequest = AdvanceRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    app_ = application_service.get_application_or_404(db, application_id)
    return pipeline_service.advance_stage(db, app_, actor_id=current_user.id, requested_to_stage=data.to_stage)


@router.post("/{application_id}/reject", response_model=ApplicationRead)
def reject_application(
    application_id: int,
    data: RejectRequest = RejectRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    app_ = application_service.get_application_or_404(db, application_id)
    return pipeline_service.reject_application(db, app_, actor_id=current_user.id, note=data.note)


@router.post("/{application_id}/reinstate", response_model=ApplicationRead)
def reinstate_application(
    application_id: int,
    data: ReinstateRequest = ReinstateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    app_ = application_service.get_application_or_404(db, application_id)
    return pipeline_service.reinstate_application(db, app_, actor_id=current_user.id, note=data.note)


@router.get("/{application_id}/history", response_model=list[HistoryEventRead])
def get_application_history(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_ = application_service.get_application_or_404(db, application_id)
    application_service.authorize_application_access(db, app_, current_user)
    return (
        db.query(ApplicationHistory)
        .filter(ApplicationHistory.application_id == application_id)
        .order_by(ApplicationHistory.created_at.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# Interview panel
# ---------------------------------------------------------------------------


@router.get("/{application_id}/interviewers", response_model=list[PanelMemberRead])
def get_panel(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_ = application_service.get_application_or_404(db, application_id)
    application_service.authorize_application_access(db, app_, current_user)
    return panel_service.list_panel(db, application_id)


@router.post("/{application_id}/interviewers", response_model=PanelMemberRead, status_code=201)
def add_interviewer(
    application_id: int,
    data: PanelAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    application_service.get_application_or_404(db, application_id)
    return panel_service.assign_interviewer(db, application_id, data.interviewer_id, actor_id=current_user.id)


@router.delete("/{application_id}/interviewers/{user_id}", status_code=204)
def remove_interviewer(
    application_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    application_service.get_application_or_404(db, application_id)
    panel_service.remove_interviewer(db, application_id, user_id, actor_id=current_user.id)


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


@router.post("/{application_id}/feedback", response_model=FeedbackRead, status_code=201)
def submit_feedback(
    application_id: int,
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    application_service.get_application_or_404(db, application_id)
    return feedback_service.submit_feedback(db, application_id, current_user.id, data.content)


@router.get("/{application_id}/feedback", response_model=list[FeedbackRead])
def get_feedback(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_ = application_service.get_application_or_404(db, application_id)
    application_service.authorize_application_access(db, app_, current_user)
    return feedback_service.list_feedback(db, application_id)


# ---------------------------------------------------------------------------
# Interview scheduling
# ---------------------------------------------------------------------------


@router.post("/{application_id}/interviews", response_model=InterviewRead, status_code=201)
def schedule_interview(
    application_id: int,
    data: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    app_ = application_service.get_application_or_404(db, application_id)
    return interview_service.schedule_interview(db, app_, data, actor_id=current_user.id)


@router.get("/{application_id}/interviews", response_model=list[InterviewRead])
def list_interviews(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_ = application_service.get_application_or_404(db, application_id)
    application_service.authorize_application_access(db, app_, current_user)
    return interview_service.list_interviews_for_application(db, application_id)

@router.delete("/{application_id}/interviews/{interview_id}", status_code=204)
def cancel_interview(
    application_id: int,
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    app_ = application_service.get_application_or_404(db, application_id)
    interview_service.cancel_interview(db, app_, interview_id, actor_id=current_user.id)