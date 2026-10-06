from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    project_id: int
    contractor_id: int
    amount: float = Field(gt=0)
    payment_date: date
    status: str
    description: str | None = None


class PaymentResponse(BaseModel):
    id: int
    project_id: int
    contractor_id: int
    amount: float
    payment_date: date
    status: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)