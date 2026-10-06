from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str
    audience: str
    expires_at: date | None = None
    created_by: int


class AlertResponse(BaseModel):
    id: int
    title: str
    message: str
    severity: str
    audience: str
    expires_at: date | None = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)