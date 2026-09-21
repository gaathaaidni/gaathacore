from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.vendor_invoice import VendorInvoiceCapture
from app.models.purchase_order import PurchaseOrder
from app.models.vendor_management import Vendor
from app.models.user import User
from app.utils.dependencies import get_db, require_roles, get_current_org_id
from app.utils.roles import (
    ROLE_ORGADMIN,
    ROLE_SUPERADMIN,
    ROLE_MANAGER,
    ROLE_LEAD,
    ROLE_PARTNER,
    ROLE_STANDARD_USER,
)

router = APIRouter(prefix="/api/v2/vendor-invoices", tags=["Vendor Invoices"])

class VendorInvoiceCaptureBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_id: Optional[int] = None
    vendor_name: str = Field(..., max_length=255)
    invoice_number: str = Field(..., max_length=100)
    purchase_order_reference: Optional[str] = Field(None, max_length=100)
    total_amount: float = Field(..., gt=0)
    currency: str = Field('USD', min_length=3, max_length=3)
    extracted_fields: Optional[dict] = None
    notes: Optional[str] = None

class VendorInvoiceCaptureCreate(VendorInvoiceCaptureBase):
    pass

class VendorInvoiceCaptureRead(VendorInvoiceCaptureBase):
    id: int
    status: str
    match_status: str
    approval_status: str
    matched_po_reference: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/", response_model=List[VendorInvoiceCaptureRead])
async def list_vendor_invoices(
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
    query = select(VendorInvoiceCapture).where(VendorInvoiceCapture.organization_id == org_id)
    if current_user.role == ROLE_SUPERADMIN:
        query = select(VendorInvoiceCapture)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=VendorInvoiceCaptureRead, status_code=status.HTTP_201_CREATED)
async def create_vendor_invoice_capture(
    invoice_in: VendorInvoiceCaptureCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    matched_po_reference = None
    match_status = 'pending'

    if invoice_in.vendor_id is not None:
        vendor_result = await db.execute(select(Vendor).where(Vendor.id == invoice_in.vendor_id, Vendor.organization_id == org_id))
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Vendor not found for this organization')
    else:
        vendor = None

    if invoice_in.purchase_order_reference:
        po_result = await db.execute(select(PurchaseOrder).where(
            PurchaseOrder.reference_number == invoice_in.purchase_order_reference,
            PurchaseOrder.org_id == org_id
        ))
        po = po_result.scalar_one_or_none()
        if po:
            matched_po_reference = po.reference_number
            if float(po.total_amount) == invoice_in.total_amount:
                match_status = 'matched'
            else:
                match_status = 'amount_mismatch'
        else:
            match_status = 'po_not_found'

    new_invoice = VendorInvoiceCapture(
        organization_id=org_id,
        vendor_id=invoice_in.vendor_id,
        vendor_name=invoice_in.vendor_name,
        invoice_number=invoice_in.invoice_number,
        purchase_order_reference=invoice_in.purchase_order_reference,
        matched_po_reference=matched_po_reference,
        total_amount=invoice_in.total_amount,
        currency=invoice_in.currency,
        extracted_fields=invoice_in.extracted_fields or {},
        notes=invoice_in.notes,
        match_status=match_status,
        approval_status='pending',
        status='matched' if match_status == 'matched' else 'pending_ocr',
    )

    db.add(new_invoice)
    await db.commit()
    await db.refresh(new_invoice)
    return new_invoice


@router.post("/{invoice_id}/approve", response_model=VendorInvoiceCaptureRead)
async def approve_vendor_invoice_capture(
    invoice_id: int,
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
    result = await db.execute(select(VendorInvoiceCapture).where(
        VendorInvoiceCapture.id == invoice_id,
        VendorInvoiceCapture.organization_id == org_id
    ))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Vendor invoice capture not found')

    if invoice.match_status != 'matched':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Unable to approve invoice unless purchase order matching is successful.'
        )

    invoice.approval_status = 'approved'
    invoice.status = 'approved'
    await db.commit()
    await db.refresh(invoice)
    return invoice
