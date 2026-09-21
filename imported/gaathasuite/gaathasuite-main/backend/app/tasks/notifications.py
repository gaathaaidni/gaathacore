from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from typing import List
from app.utils.dependencies import get_db, get_current_org_id, get_current_user_id
from app.models.notifications import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/")
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id)
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id, Notification.org_id == org_id)
        .order_by(desc(Notification.created_at))
        .limit(20)
    )
    return result.scalars().all()

@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "updated"}