import secrets
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.expenses import Vendor
from fastapi import HTTPException

class VendorInvitationService:
    @staticmethod
    async def invite_vendor(db: AsyncSession, vendor_id: int, org_id: int):
        """
        Generates a unique API key for a vendor and triggers an invitation email.
        """
        result = await db.execute(
            select(Vendor).where(Vendor.id == vendor_id, Vendor.org_id == org_id)
        )
        vendor = result.scalar_one_or_none()
        
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
            
        # Generate secure URL-safe API Key
        new_api_key = f"nx_v_{secrets.token_urlsafe(32)}"
        vendor.api_key = new_api_key
        
        # Update database
        await db.commit()
        await db.refresh(vendor)
        
        # Placeholder for Email Service integration
        # In production, this would use app.services.email.send_invitation(...)
        logging.info(f"INVITATION SENT: Vendor {vendor.name} ({vendor.email}) with Key: {new_api_key}")
        
        return {"status": "invited", "vendor_id": vendor.id, "email_sent_to": vendor.email}