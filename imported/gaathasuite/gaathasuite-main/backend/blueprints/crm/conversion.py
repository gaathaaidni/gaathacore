from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict
from app.models.crm import Lead, Customer
from app.models.books import Invoice, InvoiceLine
from app.models.user import User
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import (
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_SUPERADMIN,
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/v2/crm/conversion", tags=["CRM Conversion"])

class ConversionRequest(BaseModel):
    lead_id: int
    opening_fee: float = 0.0
    invoice_notes: str = "Opening balance/setup fee generated upon conversion."

@router.post("/convert-lead")
async def convert_lead_to_customer(
    request: ConversionRequest,
    current_user: User = Depends(require_roles(
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    Stitches CRM and Books: Converts a Lead to a Customer and creates an opening Invoice.
    """
    org_id = current_user.organization_id
    
    # 1. Fetch the Lead
    lead_stmt = select(Lead).where(Lead.id == request.lead_id, Lead.organization_id == org_id)
    res = await db.execute(lead_stmt)
    lead = res.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or unauthorized.")

    try:
        async with db.begin_nested(): # Atomic sub-transaction
            # 2. Create Customer
            new_customer = Customer(
                organization_id=org_id,
                name=lead.name,
                email=lead.contact_email,
                phone=getattr(lead, 'phone', None), # Fallback if field missing
                currency="USD"
            )
            db.add(new_customer)
            await db.flush()

            # 3. Create Opening Invoice if fee > 0
            if request.opening_fee > 0:
                new_invoice = Invoice(
                    organization_id=org_id,
                    number=f"OPN-{lead.id}-{org_id}",
                    customer_id=new_customer.id,
                    total_amount=request.opening_fee,
                    status="sent",
                    notes=request.invoice_notes
                )
                db.add(new_invoice)
                await db.flush()
                
                line = InvoiceLine(
                    organization_id=org_id,
                    invoice_id=new_invoice.id,
                    description="Onboarding / Setup Fee",
                    qty=1,
                    unit_price=request.opening_fee,
                    total=request.opening_fee
                )
                db.add(line)

            # 4. Mark Lead as converted or delete
            lead.status = "converted" 
            
        await db.commit()
        return {"status": "success", "customer_id": new_customer.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")