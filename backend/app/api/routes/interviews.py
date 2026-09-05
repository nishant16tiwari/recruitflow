from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_interviewer
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import InterviewRead
from app.services import interview_service

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("/my", response_model=list[InterviewRead])
def list_my_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    """
    Every interview this interviewer is on, across every application and
    every job opening - independent of the application-scoped
    GET /applications/{id}/interviews route, since an interviewer needs a
    single place to see their whole schedule without visiting each
    application individually.
    """
    return interview_service.list_interviews_for_interviewer(db, current_user.id)
