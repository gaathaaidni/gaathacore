from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.utils.dependencies import get_db # Assuming get_db provides AsyncSession
from app.models.books import Invoice, Payment # Assuming these models exist
from app.models.expenses import Vendor # Assuming Vendor model exists
from app.schemas.vendors import VendorInvoice, VendorPayment

router = APIRouter(prefix="/vendor-portal", tags=["Vendor Portal"])

# Placeholder for vendor authentication. In a real system, this would involve
# a dedicated vendor login, JWTs, or API keys, and the vendor_id would be
# extracted from the authenticated context.
async def get_current_vendor(vendor_id: int, org_id: int, db: AsyncSession = Depends(get_db)):
    # This is a simplified check. A real implementation would validate a token
    # and ensure the vendor is active and belongs to the org.
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.org_id == org_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=403, detail="Vendor not found or unauthorized access")
    return vendor

@router.get("/{vendor_id}/invoices", response_model=List[VendorInvoice])
async def get_vendor_invoices(
    vendor_id: int,
    org_id: int, # This would typically come from the authenticated vendor's context
    db: AsyncSession = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor) # Implicitly validates vendor
):
    # Assuming invoices can be linked to vendors (e.g., via a vendor_id on Invoice)
    # For now, we'll assume a direct link or a way to infer vendor from customer
    # This might need adjustment based on how invoices are related to vendors.
    # For this example, let's assume a direct vendor_id on Invoice for simplicity.
    result = await db.execute(
        select(Invoice).where(Invoice.org_id == org_id, Invoice.vendor_id == vendor_id) # Assuming Invoice has vendor_id
    )
    return result.scalars().all()

@router.get("/{vendor_id}/payments", response_model=List[VendorPayment])
async def get_vendor_payments(
    vendor_id: int,
    org_id: int, # This would typically come from the authenticated vendor's context
    db: AsyncSession = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor) # Implicitly validates vendor
):
    # Assuming payments can be linked to vendors (e.g., via a vendor_id on Payment)
    result = await db.execute(
        select(Payment).where(Payment.org_id == org_id, Payment.vendor_id == vendor_id) # Assuming Payment has vendor_id
    )
    return result.scalars().all()