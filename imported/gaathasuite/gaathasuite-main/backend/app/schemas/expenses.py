from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

class ExpenseBase(BaseModel):
    amount: Decimal
    category: str
    description: Optional[str] = None
    expense_date: date
    vendor_id: Optional[int] = None
    currency: str = "USD"
    receipt_url: Optional[str] = None
    status: str = "pending"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": "45.50",
                "category": "Travel",
                "description": "Taxi to airport",
                "expense_date": "2024-04-22"
            }
        }
    )

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    description: Optional[str] = None
    expense_date: Optional[date] = None
    vendor_id: Optional[int] = None
    currency: Optional[str] = None
    receipt_url: Optional[str] = None

class ExpenseRead(ExpenseBase):
    id: int
    org_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    approval_request: Optional[dict] = None  # Simplified for now
    model_config = ConfigDict(from_attributes=True)