from datetime import date

from pydantic import BaseModel, ConfigDict


class RoadCreate(BaseModel):
    location_id: int
    name: str
    length_km: float
    width_m: float
    road_condition: str
    last_maintained_date: date | None = None


class RoadResponse(BaseModel):
    id: int
    location_id: int
    name: str
    length_km: float
    width_m: float
    road_condition: str
    last_maintained_date: date | None = None

    model_config = ConfigDict(from_attributes=True)