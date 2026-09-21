from sqlalchemy import String, ForeignKey, Integer, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
from datetime import datetime
from decimal import Decimal
from typing import List

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    
    status: Mapped[str] = mapped_column(String(50), default="draft") # draft, pending_approval, ordered, received, cancelled
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.00)
    reference_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    lines: Mapped[List["POLineItem"]] = relationship(back_populates="purchase_order", cascade="all, delete-orphan")
    vendor: Mapped["Vendor"] = relationship("app.models.expenses.Vendor")

class POLineItem(Base):
    __tablename__ = "purchase_order_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="lines")
    item: Mapped["Item"] = relationship("Item")