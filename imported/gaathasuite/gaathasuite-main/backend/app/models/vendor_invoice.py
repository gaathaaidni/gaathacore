from sqlalchemy import String, Integer, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import Optional


class VendorInvoiceCapture(Base):
    __tablename__ = 'vendor_invoice_captures'

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    vendor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('vendor.id'), nullable=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    purchase_order_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    matched_po_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default='USD')
    extracted_fields: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    match_status: Mapped[str] = mapped_column(String(50), default='pending')
    approval_status: Mapped[str] = mapped_column(String(50), default='pending')
    status: Mapped[str] = mapped_column(String(50), default='pending_ocr')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vendor = relationship('app.models.vendor_management.Vendor')
