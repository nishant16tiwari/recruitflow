from pydantic import BaseModel

from app.models.enums import Stage


class AdvanceRequest(BaseModel):
    """
    to_stage is OPTIONAL. WHY: the normal UI flow never needs to specify a
    target - "advance" always means "move one step forward from wherever
    the application currently is," computed server-side. But we still
    accept an optional to_stage so that if a client (malicious or buggy)
    explicitly requests a specific stage - e.g. trying to jump
    Applied -> Offer directly - the server can validate that exact request
    and return a precise, explanatory rejection rather than silently
    reinterpreting it as "advance one step."
    """

    to_stage: Stage | None = None


class RejectRequest(BaseModel):
    note: str = ""


class ReinstateRequest(BaseModel):
    note: str = ""


class StageChangeResult(BaseModel):
    success: bool
    application_id: int
    old_stage: Stage | None = None
    new_stage: Stage | None = None
    reason: str | None = None
