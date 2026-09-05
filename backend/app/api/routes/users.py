from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_recruiter
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/interviewers", response_model=list[UserRead])
def list_interviewers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    """
    Minimal addition beyond the original spec: recruiters need a list of
    INTERVIEWER-role users to choose from when assigning a panel or
    scheduling an interview. Recruiter-only, since interviewer identities
    aren't otherwise exposed to other interviewers.
    """
    return db.query(User).filter(User.role == UserRole.INTERVIEWER).order_by(User.name).all()
