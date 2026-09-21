from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TransactionLine(BaseModel):
    item_id: int
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    tax: Decimal = Field(default=Decimal("0"), ge=0)


class QuotationCreate(BaseModel):
    customer_id: int
    quotation_number: str
    quotation_date: date
    valid_until: Optional[date] = None
    currency: str = "USD"
    notes: Optional[str] = None
    lines: list[TransactionLine] = Field(min_length=1)


class StatusUpdate(BaseModel):
    status: str


class QuotationRead(BaseModel):
    id: int
    organization_id: int
    customer_id: int
    quotation_number: str
    status: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    model_config = ConfigDict(from_attributes=True)


class SalesOrderCreate(BaseModel):
    customer_id: int
    order_number: str
    order_date: date
    currency: str = "USD"
    quotation_id: Optional[int] = None
    notes: Optional[str] = None
    lines: list[TransactionLine] = Field(min_length=1)


class SalesOrderRead(BaseModel):
    id: int
    organization_id: int
    customer_id: int
    quotation_id: Optional[int]
    order_number: str
    status: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    model_config = ConfigDict(from_attributes=True)


class FulfillmentCreate(BaseModel):
    warehouse_id: int
    fulfillment_number: str


class PurchaseReceiptLineCreate(BaseModel):
    item_id: int
    received_quantity: Decimal = Field(gt=0)


class PurchaseReceiptCreate(BaseModel):
    purchase_order_id: int
    warehouse_id: int
    receipt_number: str
    lines: list[PurchaseReceiptLineCreate] = Field(min_length=1)


class VendorBillCreate(BaseModel):
    vendor_id: int
    purchase_order_id: Optional[int] = None
    bill_number: str
    bill_date: date
    currency: str = "USD"
    subtotal: Decimal = Field(gt=0)
    tax: Decimal = Field(default=Decimal("0"), ge=0)


class BillPaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    reference: str = ""
