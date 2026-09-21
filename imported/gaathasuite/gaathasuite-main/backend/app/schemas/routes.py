from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.organization import Organization
from app.schemas.settings import OrganizationRead, OrganizationUpdate
from app.models.user import User
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import ROLE_ORGADMIN, ROLE_SUPERADMIN

router = APIRouter(prefix="/api/v2/settings", tags=["Organization Settings"])

@router.get("/", response_model=OrganizationRead)
async def get_settings(
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve settings for the current organization."""
    org_id = current_user.organization_id

    if current_user.is_superadmin and org_id is None:
        raise HTTPException(status_code=400, detail="Super Admin must specify an Org context via headers.")
    if org_id is None:
        raise HTTPException(status_code=403, detail="Organization context is missing for current user")

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.patch("/", response_model=OrganizationRead)
async def update_settings(
    settings_in: OrganizationUpdate,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Update organization details (name, address, etc)."""
    org_id = current_user.organization_id
    if current_user.is_superadmin and org_id is None:
        raise HTTPException(status_code=400, detail="Super Admin must specify an Org context via headers.")
    if org_id is None:
        raise HTTPException(status_code=403, detail="Organization context is missing for current user")

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = settings_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)
    
    await db.commit()
    await db.refresh(org)
    return org