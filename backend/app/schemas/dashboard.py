from datetime import date

from pydantic import BaseModel


class JobBreakdownItem(BaseModel):
    job_id: int
    job_title: str
    count: int


class StageBreakdownItem(BaseModel):
    stage: str
    count: int


class WeeklyApplicationPoint(BaseModel):
    week_start: date
    count: int


class DashboardResponse(BaseModel):
    open_positions: int
    active_applications: int
    interviews_this_week: int
    hires_this_month: int
    by_job_opening: list[JobBreakdownItem]
    by_stage: list[StageBreakdownItem]
    weekly_applications: list[WeeklyApplicationPoint]
