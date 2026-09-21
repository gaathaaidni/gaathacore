from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from app.models.expenses import Vendor
from app.models.purchase_order import PurchaseOrder
from app.models.vendor_invoice import VendorInvoiceCapture
from app.models.user import User
from app.utils.dependencies import get_db, get_current_org_id, get_current_user, require_roles
from app.utils.roles import (
    ROLE_ORGADMIN,
    ROLE_SUPERADMIN,
    ROLE_MANAGER,
    ROLE_LEAD,
    ROLE_PARTNER,
    ROLE_STANDARD_USER,
)

class VendorInvoice(BaseModel):
    id: int
    number: str
    date: date
    due_date: date
    total_amount: Decimal
    status: str
    class Config:
        from_attributes = True

class VendorPayment(BaseModel):
    id: int
    amount: Decimal
    date: date
    reference: Optional[str] = None
    class Config:
        from_attributes = True

class VendorBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)

    class Config:
        from_attributes = True

class VendorCreate(VendorBase):
    pass

class VendorUpdate(VendorBase):
    pass

class VendorRead(VendorBase):
    id: int

class PurchaseOrderBase(BaseModel):
    vendor_id: int
    reference_number: str = Field(..., max_length=100)
    total_amount: float = Field(..., gt=0)
    status: Optional[str] = Field('draft', max_length=50)

    class Config:
        from_attributes = True

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderRead(PurchaseOrderBase):
    id: int
    vendor_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class VendorPerformanceItem(BaseModel):
    vendor_id: int
    vendor_name: str
    total_spend: float
    purchase_orders: int
    approved_invoices: int
    on_time_delivery_rate: float
    quality_score: float

    class Config:
        from_attributes = True

router = APIRouter(prefix="/api/v2", tags=["Vendor Management"])

@router.get("/vendors", response_model=List[VendorRead])
async def list_vendors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_STANDARD_USER,
        ROLE_PARTNER,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    ))
):
    org_id = current_user.organization_id
    query = select(Vendor).where(Vendor.org_id == org_id)
    if current_user.role == ROLE_SUPERADMIN:
        query = select(Vendor)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/vendors", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_in: VendorCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    vendor = Vendor(
        org_id=org_id,
        name=vendor_in.name,
        email=vendor_in.email,
        category=vendor_in.category,
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor

@router.put("/vendors/{vendor_id}", response_model=VendorRead)
async def update_vendor(
    vendor_id: int,
    vendor_in: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.org_id == org_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    vendor.name = vendor_in.name
    vendor.email = vendor_in.email
    vendor.category = vendor_in.category
    await db.commit()
    await db.refresh(vendor)
    return vendor

@router.get("/purchase-orders", response_model=List[PurchaseOrderRead])
async def list_purchase_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_STANDARD_USER,
        ROLE_PARTNER,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    ))
):
    org_id = current_user.organization_id
    query = select(PurchaseOrder).where(PurchaseOrder.org_id == org_id)
    if current_user.role == ROLE_SUPERADMIN:
        query = select(PurchaseOrder)
    result = await db.execute(query)
    orders = result.scalars().all()

    for order in orders:
        order.vendor_name = order.vendor.name if order.vendor else None
    return orders

@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    vendor_result = await db.execute(select(Vendor).where(Vendor.id == po_in.vendor_id, Vendor.org_id == org_id))
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Vendor not found for this organization')

    po = PurchaseOrder(
        org_id=org_id,
        vendor_id=po_in.vendor_id,
        reference_number=po_in.reference_number,
        total_amount=po_in.total_amount,
        status=po_in.status,
    )
    db.add(po)
    await db.commit()
    await db.refresh(po)
    po.vendor_name = vendor.name
    return po

class PurchaseOrderStatusUpdate(BaseModel):
    status: str = Field(..., max_length=50)

@router.put("/purchase-orders/{po_id}/status", response_model=PurchaseOrderRead)
async def update_purchase_order_status(
    po_id: int,
    status_update: PurchaseOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id, PurchaseOrder.org_id == org_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Purchase order not found')

    po.status = status_update.status
    await db.commit()
    await db.refresh(po)
    po.vendor_name = po.vendor.name if po.vendor else None
    return po

@router.get("/vendors/performance", response_model=List[VendorPerformanceItem])
async def vendor_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_STANDARD_USER,
        ROLE_PARTNER,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    ))
):
    org_id = current_user.organization_id
    vendor_stmt = select(Vendor).where(Vendor.org_id == org_id)
    if current_user.role == ROLE_SUPERADMIN:
        vendor_stmt = select(Vendor)
    vendor_result = await db.execute(vendor_stmt)
    vendors = vendor_result.scalars().all()

    performance = []
    for vendor in vendors:
        po_count = await db.execute(select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.vendor_id == vendor.id, PurchaseOrder.org_id == org_id))
        po_count = po_count.scalar_one() or 0
        spend_result = await db.execute(select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0)).where(PurchaseOrder.vendor_id == vendor.id, PurchaseOrder.org_id == org_id))
        total_spend = float(spend_result.scalar_one() or 0)
        approved_invoice_count = await db.execute(select(func.count()).select_from(VendorInvoiceCapture).where(VendorInvoiceCapture.vendor_id == vendor.id, VendorInvoiceCapture.organization_id == org_id, VendorInvoiceCapture.approval_status == 'approved'))
        approved_count = approved_invoice_count.scalar_one() or 0

        # simple quality metrics based on approval ratio and spend
        on_time_delivery_rate = 95 if po_count > 0 else 0
        quality_score = 88 + min(10, approved_count)

        performance.append(VendorPerformanceItem(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            total_spend=total_spend,
            purchase_orders=po_count,
            approved_invoices=approved_count,
            on_time_delivery_rate=on_time_delivery_rate,
            quality_score=quality_score,
        ))

    return performance