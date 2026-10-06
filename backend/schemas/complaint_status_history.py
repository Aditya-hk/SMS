from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplaintStatusHistoryCreate(BaseModel):
    complaint_id: int
    old_status: str | None = None
    new_status: str
    changed_by: int
    remarks: str | None = None


class ComplaintStatusHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    old_status: str | None = None
    new_status: str
    changed_by: int
    remarks: str | None = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)