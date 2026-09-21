from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.utils.dependencies import get_db, get_current_org_id, get_current_user_id
from app.models.preferences import NotificationPreference # Assuming this is the model

router = APIRouter(prefix="/settings/notifications", tags=["Settings"])

class PreferenceUpdate(BaseModel):
    email_enabled: bool
    in_app_enabled: bool
    digest_enabled: bool

@router.get("/")
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id)
):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
    pref = result.scalar_one_or_none()
    if not pref:
        return {"email_enabled": True, "in_app_enabled": True, "digest_enabled": True}
    return pref

@router.post("/")
async def update_preferences(
    data: PreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id)
):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
    pref = result.scalar_one_or_none()
    if not pref:
        pref = NotificationPreference(user_id=user_id, org_id=org_id)
        db.add(pref)
    
    pref.email_enabled = data.email_enabled
    pref.in_app_enabled = data.in_app_enabled
    pref.digest_enabled = data.digest_enabled
    
    await db.commit()
    return {"status": "success"}