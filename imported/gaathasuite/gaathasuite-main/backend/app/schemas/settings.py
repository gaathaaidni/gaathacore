import re
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import datetime

class OrganizationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description='Default currency code')
    tax_id: Optional[str] = Field(None, max_length=100)
    invoice_notes: Optional[str] = None
    invoice_terms: Optional[str] = None
    invoice_template: str = Field('classic', description='Selected invoice design template')

class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description='Default currency code')
    tax_id: Optional[str] = Field(None, max_length=100)
    invoice_notes: Optional[str] = None
    invoice_terms: Optional[str] = None
    invoice_template: Optional[str] = Field(None, description='Selected invoice design template')
    custom_fields: Optional[dict[str, str]] = Field(None, description='Custom key-value fields for invoices')

    @model_validator(mode='before')
    def validate_tax_id(cls, values):
        tax_id = values.get('tax_id')
        if tax_id and not re.match(r'^[A-Za-z0-9\s\-,./()&]{4,30}$', tax_id):
            raise ValueError(
                'Invalid Tax ID format. It should be 4-30 characters and can include letters, numbers, and symbols like -,./()&.'
            )
        return values

class OrganizationRead(OrganizationBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime