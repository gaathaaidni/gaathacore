from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class WarehouseBase(BaseModel):
    name: str
    location: Optional[str] = None
    capacity: Optional[float] = None

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseRead(WarehouseBase):
    id: int
    organization_id: int
    model_config = ConfigDict(from_attributes=True)

class ItemBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    sale_price: float = 0.0
    purchase_cost: float = 0.0
    min_stock_level: float = 0.0

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    sale_price: Optional[float] = None

class ItemRead(ItemBase):
    id: int
    organization_id: int
    model_config = ConfigDict(from_attributes=True)

class StockRecordCreate(BaseModel):
    item_id: int
    warehouse_id: int
    quantity: float

class StockRecordRead(BaseModel):
    id: int
    item_id: int
    warehouse_id: int
    quantity: float
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

class StockAdjustment(BaseModel):
    item_id: int
    warehouse_id: int
    adjustment_qty: float
    note: Optional[str] = None

class StockTransactionRead(BaseModel):
    id: int
    organization_id: int
    item_id: int
    warehouse_id: int
    quantity: float
    transaction_type: str
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)