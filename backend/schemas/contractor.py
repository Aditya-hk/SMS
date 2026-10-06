from pydantic import BaseModel, ConfigDict


class ContractorCreate(BaseModel):
    user_id: int
    company_name: str | None = None
    license_no: str
    address: str | None = None


class ContractorResponse(BaseModel):
    user_id: int
    company_name: str | None = None
    license_no: str
    address: str | None = None

    model_config = ConfigDict(from_attributes=True)