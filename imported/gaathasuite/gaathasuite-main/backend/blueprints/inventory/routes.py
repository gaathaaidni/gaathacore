from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List

from app.models.inventory import Warehouse, Item, StockRecord, StockTransaction
from app.models.user import User
from app.schemas.inventory import (
    WarehouseCreate, WarehouseRead,
    ItemCreate, ItemRead, ItemUpdate,
    StockRecordCreate, StockRecordRead, StockAdjustment,
    StockTransactionRead
)
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import (
    ROLE_AUDITOR,
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_PARTNER,
    ROLE_STANDARD_USER,
    ROLE_SUPERADMIN,
)

router = APIRouter(prefix="/api/v2/inventory", tags=["Inventory"])

# --- Warehouse Endpoints ---
@router.get("/warehouses", response_model=List[WarehouseRead])
async def list_warehouses(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 50
):
    """List all warehouses for the current organization."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    offset = (page - 1) * limit

    query = select(Warehouse)
    if not is_god:
        query = query.where(Warehouse.organization_id == org_id)

    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()

@router.post("/warehouses", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    warehouse_in: WarehouseCreate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Create a new warehouse for the current organization."""
    org_id = current_user.organization_id
    new_warehouse = Warehouse(**warehouse_in.model_dump(), organization_id=org_id)
    db.add(new_warehouse)
    await db.commit()
    await db.refresh(new_warehouse)
    return new_warehouse

@router.get("/warehouses/{warehouse_id}", response_model=WarehouseRead)
async def get_warehouse(
    warehouse_id: int,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific warehouse."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN

    query = select(Warehouse).where(Warehouse.id == warehouse_id)
    if not is_god:
        query = query.where(Warehouse.organization_id == org_id)

    result = await db.execute(query)
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

# --- Item Endpoints ---
@router.get("/items", response_model=List[ItemRead])
async def list_items(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 50
):
    """List all inventory items for the current organization."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    offset = (page - 1) * limit

    query = select(Item)
    if not is_god:
        query = query.where(Item.organization_id == org_id)

    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()

@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_in: ItemCreate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Create a new inventory item for the current organization."""
    org_id = current_user.organization_id
    new_item = Item(**item_in.model_dump(), organization_id=org_id)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@router.get("/items/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific inventory item."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN

    query = select(Item).where(Item.id == item_id)
    if not is_god:
        query = query.where(Item.organization_id == org_id)

    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.patch("/items/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Update details of a specific inventory item."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN

    query = select(Item).where(Item.id == item_id)
    if not is_god:
        query = query.where(Item.organization_id == org_id)

    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific inventory item."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN

    query = select(Item).where(Item.id == item_id)
    if not is_god:
        query = query.where(Item.organization_id == org_id)

    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.delete(item)
    await db.commit()
    return

# --- StockRecord Endpoints ---
@router.get("/stock-records", response_model=List[StockRecordRead])
async def list_stock_records(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 50
):
    """List all stock records for the current organization."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    offset = (page - 1) * limit

    query = select(StockRecord)
    if not is_god:
        query = query.where(StockRecord.organization_id == org_id)

    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()

@router.post("/stock-records", response_model=StockRecordRead, status_code=status.HTTP_201_CREATED)
async def create_stock_record(
    stock_record_in: StockRecordCreate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Create a new stock record for the current organization."""
    org_id = current_user.organization_id
    if stock_record_in.quantity < 0:
        raise HTTPException(status_code=422, detail="Stock quantity cannot be negative")

    # Check if item and warehouse belong to the same organization
    item_query = select(Item).where(Item.id == stock_record_in.item_id, Item.organization_id == org_id)
    warehouse_query = select(Warehouse).where(Warehouse.id == stock_record_in.warehouse_id, Warehouse.organization_id == org_id)

    item_exists = (await db.execute(item_query)).scalar_one_or_none()
    warehouse_exists = (await db.execute(warehouse_query)).scalar_one_or_none()

    if not item_exists:
        raise HTTPException(status_code=404, detail="Item not found or does not belong to your organization.")
    if not warehouse_exists:
        raise HTTPException(status_code=404, detail="Warehouse not found or does not belong to your organization.")

    new_stock_record = StockRecord(**stock_record_in.model_dump(), organization_id=org_id)
    db.add(new_stock_record)
    await db.commit()
    await db.refresh(new_stock_record)
    return new_stock_record

@router.get("/stock-records/{stock_record_id}", response_model=StockRecordRead)
async def get_stock_record(
    stock_record_id: int,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific stock record."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN

    query = select(StockRecord).where(StockRecord.id == stock_record_id)
    if not is_god:
        query = query.where(StockRecord.organization_id == org_id)

    result = await db.execute(query)
    stock_record = result.scalar_one_or_none()
    if not stock_record:
        raise HTTPException(status_code=404, detail="Stock record not found")
    return stock_record

@router.post("/adjust", response_model=StockRecordRead)
async def adjust_stock(
    adjustment: StockAdjustment,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    Adjust stock levels. 
    If a record exists for the Item/Warehouse, it updates the quantity.
    If not, it creates a new record.
    """
    org_id = current_user.organization_id
    if adjustment.adjustment_qty == 0:
        raise HTTPException(status_code=422, detail="Stock adjustment cannot be zero")

    item = (await db.execute(select(Item).where(
        Item.id == adjustment.item_id, Item.organization_id == org_id
    ))).scalar_one_or_none()
    warehouse = (await db.execute(select(Warehouse).where(
        Warehouse.id == adjustment.warehouse_id, Warehouse.organization_id == org_id
    ))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or does not belong to your organization")
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found or does not belong to your organization")
    
    # Find existing record
    query = select(StockRecord).where(
        StockRecord.item_id == adjustment.item_id,
        StockRecord.warehouse_id == adjustment.warehouse_id,
        StockRecord.organization_id == org_id
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if record and record.quantity + adjustment.adjustment_qty < 0:
        raise HTTPException(status_code=409, detail="Stock cannot become negative")
    if not record and adjustment.adjustment_qty < 0:
        raise HTTPException(status_code=409, detail="Stock cannot become negative")

    if record:
        # Perform an atomic update to prevent race conditions in multi-worker environments
        await db.execute(
            update(StockRecord)
            .where(StockRecord.id == record.id)
            .values(quantity=StockRecord.quantity + adjustment.adjustment_qty)
        )
        await db.flush()
        await db.refresh(record)
    else:
        record = StockRecord(
            item_id=adjustment.item_id,
            warehouse_id=adjustment.warehouse_id,
            quantity=adjustment.adjustment_qty,
            organization_id=org_id
        )
        db.add(record)

    # Log transaction history
    transaction = StockTransaction(
        organization_id=org_id,
        item_id=adjustment.item_id,
        warehouse_id=adjustment.warehouse_id,
        quantity=adjustment.adjustment_qty,
        transaction_type="ADJUSTMENT",
        note=adjustment.note
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(record)
    return record

@router.get("/items/{item_id}/transactions", response_model=List[StockTransactionRead])
async def get_item_transactions(
    item_id: int,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 50
):
    """Fetch transaction history for a specific item."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    offset = (page - 1) * limit

    query = select(StockTransaction).where(StockTransaction.item_id == item_id)
    if not is_god:
        query = query.where(StockTransaction.organization_id == org_id)

    result = await db.execute(query.order_by(StockTransaction.created_at.desc()).offset(offset).limit(limit))
    return result.scalars().all()