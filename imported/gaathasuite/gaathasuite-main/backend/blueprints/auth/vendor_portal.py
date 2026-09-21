from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.models.procurement import Vendor, PurchaseOrder
from app.utils.dependencies import get_db

router = APIRouter(prefix="/api/v2/vendor/portal", tags=["Vendor Portal"])

@router.get("/{token}/orders")
async def get_vendor_orders(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Public endpoint for vendors to check PO status via unique token."""
    # 1. Validate Token and Find Vendor
    vendor_stmt = select(Vendor).where(Vendor.portal_token == token)
    vendor_res = await db.execute(vendor_stmt)
    vendor = vendor_res.scalar_one_or_none()
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Invalid access token.")

    if vendor.expires_at and vendor.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Portal access has expired.")

    # 2. Fetch Orders
    po_stmt = select(PurchaseOrder).where(
        PurchaseOrder.vendor_id == vendor.id
    ).options(selectinload(PurchaseOrder.line_items)).order_by(PurchaseOrder.created_at.desc())
    
    po_res = await db.execute(po_stmt)
    orders = po_res.scalars().all()
    
    return {
        "vendor_name": vendor.name,
        "orders": [
            {"number": po.po_number, "status": po.status, "date": po.order_date, "total": po.total_amount}
            for po in orders
        ]
    }