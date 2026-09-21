from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Quotation(Base):
    __tablename__ = "quotations"

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    quotation_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    quotation_date: Mapped[date] = mapped_column(Date, default=date.today)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lines: Mapped[list["QuotationLine"]] = relationship(cascade="all, delete-orphan", back_populates="quotation")


class QuotationLine(Base):
    __tablename__ = "quotation_lines"

    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    description: Mapped[str] = mapped_column(String(300))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    quotation: Mapped[Quotation] = relationship(back_populates="lines")


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quotations.id"), nullable=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    order_date: Mapped[date] = mapped_column(Date, default=date.today)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lines: Mapped[list["SalesOrderLine"]] = relationship(cascade="all, delete-orphan", back_populates="order")


class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"

    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    description: Mapped[str] = mapped_column(String(300))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    fulfilled_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    order: Mapped[SalesOrder] = relationship(back_populates="lines")


class Fulfillment(Base):
    __tablename__ = "fulfillments"

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouse.id"))
    fulfillment_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    fulfilled_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PurchaseReceipt(Base):
    __tablename__ = "purchase_receipts"

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouse.id"))
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    received_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    lines: Mapped[list["PurchaseReceiptLine"]] = relationship(cascade="all, delete-orphan", back_populates="receipt")


class PurchaseReceiptLine(Base):
    __tablename__ = "purchase_receipt_lines"

    receipt_id: Mapped[int] = mapped_column(ForeignKey("purchase_receipts.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    ordered_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    receipt: Mapped[PurchaseReceipt] = relationship(back_populates="lines")


class VendorBill(Base):
    __tablename__ = "vendor_bills"

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    bill_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    bill_date: Mapped[date] = mapped_column(Date, default=date.today)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")


class VendorBillPayment(Base):
    __tablename__ = "vendor_bill_payments"

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    vendor_bill_id: Mapped[int] = mapped_column(ForeignKey("vendor_bills.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_date: Mapped[date] = mapped_column(Date, default=date.today)
    reference: Mapped[str] = mapped_column(String(255), default="")
