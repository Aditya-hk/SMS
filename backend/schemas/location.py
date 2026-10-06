from pydantic import BaseModel, ConfigDict


class LocationCreate(BaseModel):
    area_name: str
    ward: str
    pincode: str


class LocationResponse(BaseModel):
    id: int
    area_name: str
    ward: str
    pincode: str

    model_config = ConfigDict(from_attributes=True)