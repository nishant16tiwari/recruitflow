from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.auth import UserRead


class InterviewCreate(BaseModel):
    date: date
    start_time: time
    end_time: time
    interviewer_ids: list[int] = Field(min_length=1)
    interview_type: str = "Video Call"
    location: str | None = None
    meeting_link: str | None = None

    @model_validator(mode="after")
    def check_times(self) -> "InterviewCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class InterviewRead(BaseModel):
    id: int
    application_id: int
    date: date
    start_time: time
    end_time: time
    interview_type: str
    location: str | None
    meeting_link: str | None
    created_by: int
    created_at: datetime
    interviewers: list[UserRead] = []

    model_config = ConfigDict(from_attributes=True)
