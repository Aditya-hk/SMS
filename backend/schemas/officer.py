from pydantic import BaseModel, ConfigDict


class OfficerCreate(BaseModel):
    user_id: int
    department: str | None = None
    designation: str | None = None


class OfficerResponse(BaseModel):
    user_id: int
    department: str | None = None
    designation: str | None = None

    model_config = ConfigDict(from_attributes=True)