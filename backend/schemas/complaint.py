from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ComplaintCreate(BaseModel):
    citizen_id: int
    title: str
    description: str
    category: str
    location_id: int
    complaint_date: date
    status: str = "SUBMITTED"
    assigned_officer_id: int | None = None


class ComplaintResponse(BaseModel):
    id: int
    citizen_id: int
    title: str
    description: str
    category: str
    location_id: int
    complaint_date: date
    status: str
    assigned_officer_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)