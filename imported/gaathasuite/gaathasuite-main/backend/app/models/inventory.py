from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, func, UniqueConstraint
from datetime import datetime
from typing import Optional, List
from app.models.base import Base

class Warehouse(Base):
    __tablename__ = 'warehouse'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    capacity: Mapped[Optional[float]] = mapped_column(Float)

    stock_records: Mapped[List["StockRecord"]] = relationship(back_populates="warehouse")

class Item(Base):
    __tablename__ = 'items'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    sku: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    sale_price: Mapped[float] = mapped_column(Float, default=0.0)
    purchase_cost: Mapped[float] = mapped_column(Float, default=0.0)
    min_stock_level: Mapped[float] = mapped_column(Float, default=0.0)

    stock_records: Mapped[List["StockRecord"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('organization_id', 'sku', name='_org_sku_uc'),
    )

class StockRecord(Base):
    __tablename__ = 'stock_record'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouse.id'), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    item: Mapped["Item"] = relationship(back_populates="stock_records")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="stock_records")

class StockTransaction(Base):
    __tablename__ = 'stock_transaction'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouse.id'), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    transaction_type: Mapped[str] = mapped_column(String(50)) # e.g., 'ADJUSTMENT'
    note: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())