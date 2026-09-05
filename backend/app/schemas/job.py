from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JobStatus


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: str = Field(min_length=1, max_length=255)
    description: str = ""


class JobUpdate(BaseModel):
    """
    All fields optional: WHY - this is a partial-update (PATCH) schema, so a
    client can send only the fields it wants to change. Status is deliberately
    NOT editable here; archive/restore are separate, explicit endpoints
    because they have their own business rules (applications survive
    archiving) and deserve dedicated audit-friendly actions rather than a
    generic "set status to whatever" field.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class JobRead(BaseModel):
    id: int
    title: str
    department: str
    description: str
    status: JobStatus
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobReadWithCount(JobRead):
    application_count: int
