from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Stage


class AlertItem(BaseModel):
    application_id: int
    candidate_name: str
    job_id: int
    job_title: str
    current_stage: Stage
    stage_entered_at: datetime
    days_in_stage: int


class AlertListResponse(BaseModel):
    count: int
    alerts: list[AlertItem]
