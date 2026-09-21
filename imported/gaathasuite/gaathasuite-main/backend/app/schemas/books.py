from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime, date
from typing import Optional

class InvoiceRead(BaseModel):
    id: int
    number: str
    customer_id: int
    status: str
    total_amount: float
    paid_amount: float = 0
    outstanding_amount: float = 0
    date: date
    due_date: Optional[date] = None
    currency: str
    organization_id: int
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class AccountCreate(BaseModel):
    name: str
    type: str
    code: str

class AccountRead(BaseModel):
    id: int
    organization_id: int
    name: str
    type: str
    code: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EntityCreate(BaseModel):
    name: str
    entity_type: str = Field("Subsidiary", description="Type of entity")
    base_currency: str = Field("USD", min_length=3, max_length=3, description="Entity base currency")
    supported_currencies: list[str] = Field(default_factory=lambda: ["USD"], description="Supported currencies for this entity")
    is_active: bool = Field(True, description="Whether the entity is active")

    @field_validator('base_currency', 'supported_currencies', mode='before')
    @classmethod
    def validate_currency_fields(cls, v, info):
        if info.field_name == 'supported_currencies':
            values = v if isinstance(v, list) else [v]
            validated = []
            for currency in values:
                if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
                    raise ValueError('Each supported currency must be a 3-letter code')
                validated.append(currency.upper())
            return validated
        if isinstance(v, str):
            if len(v) != 3 or not v.isalpha():
                raise ValueError('Currency must be a 3-letter code (e.g., USD, EUR, GBP)')
            return v.upper()
        return v

class EntityRead(EntityCreate):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InvoiceLineCreate(BaseModel):
    description: str
    qty: float
    unit_price: float

class InvoiceCreate(BaseModel):
    number: str
    customer_id: int
    date: date
    due_date: Optional[date] = None
    currency: str = Field("USD", min_length=3, max_length=3, description="Invoice currency")
    status: str = "draft"
    notes: Optional[str] = Field(None)
    lines: list[InvoiceLineCreate] = Field(default_factory=list)

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter code (e.g., USD, EUR, GBP)")
        return v.upper()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "number": "INV-2024-001",
                "customer_id": 1,
                "date": "2024-04-22",
                "currency": "USD",
                "lines": [{"description": "Service Fee", "qty": 1, "unit_price": 500.0}]
            }
        }
    )

class InvoiceUpdate(BaseModel):
    number: Optional[str] = None
    customer_id: Optional[int] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None