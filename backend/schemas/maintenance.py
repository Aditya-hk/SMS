from datetime import date

from pydantic import BaseModel, ConfigDict


class MaintenanceCreate(BaseModel):
    project_id: int | None = None
    road_id: int | None = None
    pipeline_id: int | None = None

    description: str
    status: str
    maintenance_date: date

    assigned_contractor_id: int
    assigned_officer_id: int


class MaintenanceResponse(BaseModel):
    id: int
    project_id: int | None = None
    road_id: int | None = None
    pipeline_id: int | None = None

    description: str
    status: str
    maintenance_date: date

    assigned_contractor_id: int
    assigned_officer_id: int

    model_config = ConfigDict(from_attributes=True)