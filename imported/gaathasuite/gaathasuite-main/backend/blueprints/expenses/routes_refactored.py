from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import date

from app.models.expenses import Expense, Vendor
from app.schemas.expenses import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.schemas.vendors import VendorCreate, VendorRead
from app.utils.dependencies import get_db, get_current_user, require_roles, get_current_org_id
from app.models.user import User
from app.utils.roles import (
    ROLE_AUDITOR,
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_PARTNER,
    ROLE_STANDARD_USER,
    ROLE_SUPERADMIN,
)

router = APIRouter(prefix="/api/v2/expenses", tags=["Expenses"])


@router.get("/vendors", response_model=List[VendorRead])
async def list_vendors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
):
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    query = select(Vendor)
    if not is_god:
        query = query.where(Vendor.org_id == org_id)

    result = await db.execute(query.order_by(Vendor.id))
    return result.scalars().all()


@router.post("/vendors", response_model=VendorRead, status_code=201)
async def create_vendor(
    vendor_in: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
):
    vendor = Vendor(
        org_id=current_user.organization_id,
        name=vendor_in.name,
        email=vendor_in.email,
        category=vendor_in.category,
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor

@router.get("/", response_model=List[ExpenseRead])
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    vendor_id: Optional[int] = None,
    category: Optional[str] = None,
    expense_status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    
    query = select(Expense)
    if not is_god:
        query = query.where(Expense.org_id == org_id)
    
    if vendor_id:
        query = query.where(Expense.vendor_id == vendor_id)
    if category:
        query = query.where(Expense.category == category)
    if expense_status:
        query = query.where(Expense.status == expense_status)
    if date_from:
        query = query.where(Expense.expense_date >= date_from)
    if date_to:
        query = query.where(Expense.expense_date <= date_to)
    
    query = query.order_by(Expense.expense_date.desc()).offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    expenses = result.scalars().all()
    
    return expenses

@router.post("/", response_model=ExpenseRead, status_code=201)
async def create_expense(
    expense: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
):
    org_id = current_user.organization_id
    
    db_expense = Expense(
        **expense.model_dump(exclude={"status"}),
        org_id=org_id,
        created_by=current_user.id,
        status=expense.status or "pending",
    )
    
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    
    return db_expense

@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
):
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.org_id == org_id if not is_god else True)
    )
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return expense

@router.put("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
):
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.org_id == org_id if not is_god else True)
    )
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    for field, value in expense_update.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    
    await db.commit()
    await db.refresh(expense)
    
    return expense

@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
):
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.org_id == org_id if not is_god else True)
    )
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    await db.delete(expense)
    await db.commit()
    
    return {"message": "Expense deleted successfully"}
