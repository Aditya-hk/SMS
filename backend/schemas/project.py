from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None

    location_id: int
    road_id: int | None = None
    pipeline_id: int | None = None

    officer_id: int
    contractor_id: int

    budget: float = Field(gt=0)

    start_date: date
    expected_completion_date: date
    actual_completion_date: date | None = None

    status: str
    progress_percent: int = Field(default=0, ge=0, le=100)

    remarks: str | None = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str | None = None

    location_id: int
    road_id: int | None = None
    pipeline_id: int | None = None

    officer_id: int
    contractor_id: int

    budget: float

    start_date: date
    expected_completion_date: date
    actual_completion_date: date | None = None

    status: str
    progress_percent: int
    remarks: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)