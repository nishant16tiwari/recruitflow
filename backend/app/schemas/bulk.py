from pydantic import BaseModel, Field

from app.models.enums import Stage


class BulkActionRequest(BaseModel):
    application_ids: list[int] = Field(min_length=1, max_length=500)


class BulkActionResult(BaseModel):
    application_id: int
    success: bool
    old_stage: Stage | None = None
    new_stage: Stage | None = None
    reason: str | None = None


class BulkActionResponse(BaseModel):
    results: list[BulkActionResult]
