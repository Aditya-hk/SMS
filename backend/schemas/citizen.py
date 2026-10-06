from pydantic import BaseModel, ConfigDict


class CitizenCreate(BaseModel):
    user_id: int
    address: str | None = None
    ward: str | None = None


class CitizenResponse(BaseModel):
    user_id: int
    address: str | None = None
    ward: str | None = None

    model_config = ConfigDict(from_attributes=True)