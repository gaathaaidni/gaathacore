from typing import Optional

from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.utils.auth import verify_token
from app.utils.roles import ROLE_SUPERADMIN, canonical_role


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """Resolve the authenticated user from the bearer access token."""
    from app.models.user import User

    payload = verify_token(token)
    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where((User.username == username) | (User.email == username))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return user


async def get_current_user_id(current_user=Depends(get_current_user)) -> int:
    """Return the authenticated user's database id."""
    return current_user.id


async def get_current_org_id(current_user=Depends(get_current_user)) -> int:
    """Return the authenticated user's organization id."""
    org_id = getattr(current_user, "organization_id", None)
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context is missing for current user",
        )
    return org_id


def require_roles(*allowed_roles: str):
    """Create a dependency that permits only users with one of the given roles."""
    allowed = {canonical_role(role) for role in allowed_roles}

    async def _require_roles(current_user=Depends(get_current_user)):
        if canonical_role(getattr(current_user, "role", "")) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _require_roles


async def get_current_user_ws(
    websocket: WebSocket, db: AsyncSession = Depends(get_db)
):
    """Resolve the authenticated user from a WebSocket session cookie."""
    from app.models.user import User

    session_cookie = websocket.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = verify_token(session_cookie)
    username = payload.get("sub") if payload else None
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    result = await db.execute(
        select(User).where((User.username == username) | (User.email == username))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_org_db_session(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the active async session plus the current org and whether the caller is God."""
    org_id = getattr(current_user, "organization_id", None)
    is_god = canonical_role(getattr(current_user, "role", "")) == ROLE_SUPERADMIN
    if org_id is None and not is_god:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context is missing for current user",
        )
    return db, org_id, is_god


async def get_redis():
    # Placeholder for a proper Redis connection dependency.
    return None
