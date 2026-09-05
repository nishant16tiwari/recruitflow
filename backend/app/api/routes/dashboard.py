from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_recruiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    return dashboard_service.get_dashboard(db)
