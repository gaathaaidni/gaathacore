from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime

class ApprovalRequestBase(BaseModel):
    document_type: str
    document_id: int
    amount: Optional[Decimal] = None
    status: str = "pending"
    reason: Optional[str] = None

class ApprovalRequestCreate(ApprovalRequestBase):
    requested_by_user_id: int

class ApprovalRequestRead(ApprovalRequestBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None