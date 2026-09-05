from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    content: str = Field(min_length=1)


class FeedbackRead(BaseModel):
    id: int
    application_id: int
    interviewer_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
