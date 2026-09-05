from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_recruiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.alert import AlertListResponse
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    alerts = alert_service.get_active_alerts(db)
    return AlertListResponse(count=len(alerts), alerts=alerts)


@router.post("/{application_id}/dismiss", status_code=204)
def dismiss_alert(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    alert_service.dismiss_alert(db, application_id, dismissed_by=current_user.id)
