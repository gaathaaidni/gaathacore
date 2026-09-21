from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.inventory import Item, Warehouse, StockRecord
from app.models.user import User
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
from app.schemas.inventory import ItemRead, ItemCreate, WarehouseRead, WarehouseCreate

router = APIRouter(prefix="/api/v2/inventory", tags=["Inventory"])

@router.get("/items", response_model=List[ItemRead])
async def list_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    ))
):
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    query = select(Item)
    if not is_god:
        query = query.where(Item.organization_id == org_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    ))
):
    org_id = current_user.organization_id
    new_item = Item(**item_in.model_dump(), organization_id=org_id)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@router.get("/warehouses", response_model=List[WarehouseRead])
async def list_warehouses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    ))
):
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    query = select(Warehouse)
    if not is_god:
        query = query.where(Warehouse.organization_id == org_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/warehouses", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    warehouse_in: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    ))
):
    org_id = current_user.organization_id
    new_warehouse = Warehouse(**warehouse_in.model_dump(), organization_id=org_id)
    db.add(new_warehouse)
    await db.commit()
    await db.refresh(new_warehouse)
    return new_warehouse