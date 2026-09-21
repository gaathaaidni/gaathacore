from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.models.base import Base
from app.utils.dependencies import get_db, get_current_org_id
from datetime import datetime, timedelta
from functools import wraps

_rate_limit_requests: dict[str, list[datetime]] = {}


def rate_limit(limit: int = 5, period_seconds: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            key = f"{client_ip}:{request.url.path}"
            now = datetime.utcnow()
            window = _rate_limit_requests.get(key, [])
            window = [ts for ts in window if now - ts < timedelta(seconds=period_seconds)]
            if len(window) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests, please try again later."
                )
            window.append(now)
            _rate_limit_requests[key] = window
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

class Vendor(Base):
    __tablename__ = 'vendor'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.post("/{vendor_id}/invite")
@rate_limit(limit=5, period_seconds=60)
async def invite_vendor_endpoint(
    request: Request,
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    """
    Triggers vendor invitation and API key generation.
    Rate-limited to 5 requests per minute per user/IP.
    """
    from app.models.vendor_service import VendorInvitationService
    return await VendorInvitationService.invite_vendor(db, vendor_id, org_id)