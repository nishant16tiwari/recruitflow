from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Stage


class ApplicationCreate(BaseModel):
    job_id: int
    candidate_name: str = Field(min_length=1, max_length=255)
    candidate_email: EmailStr
    source: str = Field(default="Other", max_length=100)
    notes: str = ""
    applied_date: date | None = None


class ApplicationUpdate(BaseModel):
    """
    Deliberately excludes current_stage - stage changes ALWAYS go through
    the dedicated /advance, /reject, /reinstate endpoints, never through a
    generic field update. This is what makes it structurally impossible to
    skip stage-transition validation by just PATCHing the stage field.
    """

    candidate_name: str | None = Field(default=None, min_length=1, max_length=255)
    candidate_email: EmailStr | None = None
    source: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class ApplicationRead(BaseModel):
    id: int
    job_id: int
    candidate_name: str
    candidate_email: str
    source: str
    notes: str
    applied_date: date
    current_stage: Stage
    previous_stage_before_rejection: Stage | None
    stage_entered_at: datetime
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
