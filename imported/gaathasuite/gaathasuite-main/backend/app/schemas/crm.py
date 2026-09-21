from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerRead(CustomerBase):
    id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True)

class LeadRead(BaseModel):
    id: int
    name: str
    contact_email: str
    company: Optional[str] = None
    status: str = "New"

    model_config = ConfigDict(from_attributes=True)


class LeadCreate(BaseModel):
    name: str
    contact_email: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None


class OpportunityCreate(BaseModel):
    title: str
    customer_id: int
    value: float = 0.0
    stage: str = "prospect"


class OpportunityRead(OpportunityCreate):
    id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True)


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None