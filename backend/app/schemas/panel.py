from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.auth import UserRead


class PanelAssignRequest(BaseModel):
    interviewer_id: int


class PanelMemberRead(BaseModel):
    id: int
    application_id: int
    interviewer_id: int
    assigned_at: datetime
    interviewer: UserRead

    model_config = ConfigDict(from_attributes=True)
