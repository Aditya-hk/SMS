from pydantic import BaseModel, ConfigDict


class PipelineCreate(BaseModel):
    location_id: int
    name: str
    pipeline_type: str
    length_km: float
    status: str
    installed_year: int


class PipelineResponse(BaseModel):
    id: int
    location_id: int
    name: str
    pipeline_type: str
    length_km: float
    status: str
    installed_year: int

    model_config = ConfigDict(from_attributes=True)