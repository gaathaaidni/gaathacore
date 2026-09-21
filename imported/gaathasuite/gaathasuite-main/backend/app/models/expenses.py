from sqlalchemy import String, ForeignKey, Numeric, Text, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.approvals import ApprovalRequest

class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    api_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100)) # e.g., Utilities, Logistics
    
    expenses: Mapped[list["Expense"]] = relationship(back_populates="vendor")

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    vendor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vendors.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    description: Mapped[Optional[str]] = mapped_column(Text)
    expense_date: Mapped[date] = mapped_column(Date, default=func.current_date())
    category: Mapped[str] = mapped_column(String(100))
    
    # For receipt upload support
    receipt_url: Mapped[Optional[str]] = mapped_column(String(1024))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    vendor: Mapped["Vendor"] = relationship("app.models.expenses.Vendor", back_populates="expenses")
