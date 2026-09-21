"""
Pydantic schemas for API request/response validation and serialization.
This provides type-safe validation for all API inputs and outputs.
"""
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime, date


# ==================== CRM SCHEMAS ====================

class CustomerBase(BaseModel):
    """Base schema for customer data."""
    name: str = Field(..., min_length=1, max_length=200, description="Customer name")
    email: Optional[EmailStr] = Field(None, description="Customer email address")
    phone: Optional[str] = Field(None, max_length=20, description="Customer phone number")
    address: Optional[str] = Field(None, max_length=300, description="Customer address")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format."""
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter code (e.g., USD, EUR, GBP)")
        return v.upper()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Acme Corp",
                "email": "contact@acme.com",
                "phone": "+1-555-0100",
                "address": "123 Main St, City, Country",
                "currency": "USD"
            }
        }
    )

class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=300)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    status: Optional[str] = Field(None, description="Customer status")


class CustomerResponse(CustomerBase):
    """Schema for customer API response."""
    id: int
    status: str = Field("active", description="Customer status")
    lifetime_value: float = Field(0.0, description="Total revenue from customer")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CustomerRead(CustomerBase):
    """Schema for reading customer data."""
    id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LeadBase(BaseModel):
    """Base schema for lead data."""
    name: str = Field(..., min_length=1, max_length=200, description="Lead name")
    contact_email: Optional[EmailStr] = Field(None, description="Lead contact email")
    source: Optional[str] = Field(None, max_length=100, description="Lead source")
    status: str = Field("new", description="Lead status")
    score: int = Field(0, ge=0, le=100, description="Lead score (0-100)")
    customer_id: Optional[int] = Field(None, description="Associated customer ID")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate lead status."""
        valid_statuses = ["new", "contacted", "qualified", "lost"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Smith",
                "contact_email": "john@example.com",
                "source": "web",
                "status": "new",
                "score": 75
            }
        }
    )

class LeadCreate(LeadBase):
    """Schema for creating a new lead."""
    pass


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_email: Optional[EmailStr] = None
    source: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    customer_id: Optional[int] = None


class LeadResponse(LeadBase):
    """Schema for lead API response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OpportunityBase(BaseModel):
    """Base schema for opportunity data."""
    title: str = Field(..., min_length=1, max_length=200, description="Opportunity title")
    customer_id: int = Field(..., description="Customer ID")
    value: float = Field(0.0, ge=0, description="Opportunity value")
    stage: str = Field("prospect", description="Sales stage")
    probability: int = Field(50, ge=0, le=100, description="Win probability (0-100)")
    expected_close_date: Optional[date] = Field(None, description="Expected close date")
    
    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v: str) -> str:
        """Validate opportunity stage."""
        valid_stages = ["prospect", "negotiation", "won", "lost"]
        if v not in valid_stages:
            raise ValueError(f"Stage must be one of: {valid_stages}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Large Enterprise Deal",
                "customer_id": 1,
                "value": 50000.00,
                "stage": "negotiation",
                "probability": 75,
                "expected_close_date": "2026-03-31"
            }
        }
    )

class OpportunityCreate(OpportunityBase):
    """Schema for creating a new opportunity."""
    pass


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    value: Optional[float] = Field(None, ge=0)
    stage: Optional[str] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[date] = None


class OpportunityResponse(OpportunityBase):
    """Schema for opportunity API response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ==================== BOOKS (ACCOUNTING) SCHEMAS ====================

class InvoiceLineBase(BaseModel):
    """Base schema for invoice line item."""
    description: Optional[str] = Field(None, max_length=300)
    qty: float = Field(1.0, gt=0, description="Quantity")
    unit_price: float = Field(0.0, ge=0, description="Unit price")


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line items."""
    total: Optional[float] = Field(None, description="Auto-calculated if not provided")
    
    @field_validator('total', mode='before')
    @classmethod
    def calculate_total(cls, v: Optional[float], info) -> float:
        """Calculate total from qty and unit_price if not provided."""
        # In V2, we usually calculate this in a @model_validator or 
        # handle it in the database/service layer. 
        # For now, we return the value as-is to satisfy the schema.
        if v is None and 'qty' in info.data and 'unit_price' in info.data:
            return info.data['qty'] * info.data['unit_price']
        return v


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line item API response."""
    id: int
    invoice_id: int
    total: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class InvoiceBase(BaseModel):
    """Base schema for invoice data."""
    number: str = Field(..., min_length=1, max_length=50, description="Invoice number")
    customer_id: int = Field(..., description="Customer ID")
    invoice_date: date = Field(default_factory=date.today, description="Invoice date")
    due_date: Optional[date] = None
    status: str = Field("draft", description="Invoice status")
    notes: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate invoice status."""
        valid_statuses = ["draft", "sent", "paid", "overdue"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure due date is after invoice date."""
        if v and 'invoice_date' in info.data and v < info.data['invoice_date']:
            raise ValueError("Due date must be after invoice date")
        return v


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    lines: list[InvoiceLineCreate] = Field(default_factory=list, description="Invoice line items")
    model_config = ConfigDict(from_attributes=True)

class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    number: Optional[str] = None
    customer_id: Optional[int] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice API response."""
    id: int
    total_amount: float = Field(0.0, description="Total invoice amount")
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ==================== PAGINATION ====================

class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(50, ge=1, le=500, description="Items per page (max 500)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "limit": 50
            }
        }
    )

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    data: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [],
                "total": 100,
                "page": 1,
                "limit": 50,
                "pages": 2
            }
        }
    )
