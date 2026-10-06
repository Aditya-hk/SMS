from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ProjectProgressCreate(BaseModel):
    project_id: int
    progress_percent: int = Field(ge=0, le=100)
    progress_date: date
    remarks: str | None = None
    updated_by: int


class ProjectProgressResponse(BaseModel):
    id: int
    project_id: int
    progress_percent: int
    progress_date: date
    remarks: str | None = None
    updated_by: int

    model_config = ConfigDict(from_attributes=True)