from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.crm import Lead, Customer
from app.models.books import Invoice, InvoiceLine
from fastapi import HTTPException

class CRMConversionService:
    @staticmethod
    async def convert_lead_to_invoice(db: AsyncSession, lead_id: int, org_id: int):
        """
        Atomic process: 
        1. Validate Lead
        2. Create Customer record
        3. Create Invoice
        4. Update Lead status to 'Converted'
        """
        # 1. Fetch Lead within the tenant context
        result = await db.execute(
            select(Lead).where(Lead.id == lead_id, Lead.org_id == org_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found or unauthorized")
        
        # 2. Create Customer
        new_customer = Customer(
            org_id=org_id,
            name=lead.contact_name or lead.company_name,
            email=lead.email,
            phone=lead.phone,
            lead_source=lead.source
        )
        db.add(new_customer)
        await db.flush() # Get ID for the invoice

        # 3. Create Invoice (Initial Draft)
        new_invoice = Invoice(
            org_id=org_id,
            customer_id=new_customer.id,
            status="draft",
            total_amount=lead.estimated_value or 0.00,
            reference=f"CONV-LEAD-{lead.id}"
        )
        db.add(new_invoice)

        # 4. Update Lead Status
        lead.status = "converted"
        lead.converted_customer_id = new_customer.id
        
        try:
            await db.commit()
            return {"customer_id": new_customer.id, "invoice_id": new_invoice.id}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")