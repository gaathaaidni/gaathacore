from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.db import AsyncSessionLocal
from sqlalchemy import insert
from app.models.base import ActivityLog  # Assuming it's moved or adapted
import logging
import asyncio

logger = logging.getLogger(__name__)

class ActivityLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only log state-changing operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"] and response.status_code < 400:
            # Extract user_id and org_id from request state (set by auth middleware)
            user_id = getattr(request.state, 'user_id', None)
            org_id = getattr(request.state, 'org_id', None)
            
            if user_id and org_id:
                action = f"{request.method} {request.url.path}"
                details = f"Status: {response.status_code}"
                
                # Log to database asynchronously
                asyncio.create_task(self._log_activity(org_id, user_id, action, details))
        
        return response
    
    async def _log_activity(self, org_id: int, user_id: int, action: str, details: str):
        try:
            async with AsyncSessionLocal() as session:
                # Assuming ActivityLog is adapted to async
                activity_log = ActivityLog(
                    user_id=user_id,
                    organization_id=org_id,
                    action=action,
                    details=details
                )
                session.add(activity_log)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")