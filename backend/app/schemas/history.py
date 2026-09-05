from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import HistoryEventType, Stage


class HistoryEventRead(BaseModel):
    id: int
    application_id: int
    event_type: HistoryEventType
    from_stage: Stage | None
    to_stage: Stage | None
    actor_id: int
    note: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
