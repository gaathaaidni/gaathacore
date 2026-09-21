from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_org_id, get_current_user_id
from app.models.base import ScheduledReport
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/reports/schedule", tags=["Reports"])

class ScheduleCreate(BaseModel):
    report_name: str
    report_type: str # "EXPORT" or "DIGEST"
    resource_type: str = None
    frequency: str # "DAILY" or "WEEKLY"

@router.post("/")
async def schedule_report(
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user_id: int = Depends(get_current_user_id)
):
    next_run = datetime.utcnow() + (timedelta(days=1) if data.frequency == "DAILY" else timedelta(days=7))
    
    new_schedule = ScheduledReport(
        org_id=org_id,
        user_id=user_id,
        report_name=data.report_name,
        report_type=data.report_type,
        resource_type=data.resource_type,
        frequency=data.frequency,
        next_run_at=next_run
    )
    
    db.add(new_schedule)
    await db.commit()
    return {"status": "Scheduled", "next_run": next_run}