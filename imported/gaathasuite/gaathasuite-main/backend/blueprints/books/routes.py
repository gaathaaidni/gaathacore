from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit import SettingsChangeLog
from app.models.organization import Organization
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.settings import OrganizationRead, OrganizationUpdate
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import (
    ROLE_ORGADMIN,
    ROLE_SUPERADMIN,
)

router = APIRouter(prefix="/api/v2/settings", tags=["Organization Settings"])

@router.get("/", response_model=OrganizationRead)
async def get_settings(
    current_user: User = Depends(require_roles(
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve settings for the current organization."""
    org_id = current_user.organization_id
    if current_user.role == ROLE_SUPERADMIN: # Super Admin should not access specific org settings without context
        raise HTTPException(status_code=400, detail="Super Admin must specify an Org context via headers.")

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.patch("/", response_model=OrganizationRead)
async def update_settings(
    settings_in: OrganizationUpdate,
    current_user: User = Depends(require_roles(
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """Update organization details (name, address, etc)."""
    org_id = current_user.organization_id
    
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    
    update_data = settings_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        # Only update if the value has actually changed
        if getattr(org, key) != value:
            setattr(org, key, value)
    
    if db.is_modified(org):
        try:
            # Log the change
            log_entry = SettingsChangeLog(
                organization_id=org_id,
                user_id=current_user.id,
                changes=update_data
            )
            db.add(log_entry)
            
            await db.commit()
            await db.refresh(org)
            
            await NotificationService.send_settings_change_email(db, org_id, current_user, update_data)
            return org
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save settings and log changes.")
    
    return org