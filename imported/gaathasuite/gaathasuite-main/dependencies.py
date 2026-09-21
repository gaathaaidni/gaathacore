from fastapi import Depends, WebSocket, HTTPException, status
from sqlalchemy import select

# Assuming your User model and database session logic are here
from app.models.user import User
from app.db.session import get_db

# Placeholder for your JWT or session validation logic
from app.core.security import decode_access_token


async def get_current_user_ws(websocket: WebSocket, db: AsyncSession = Depends(get_db)) -> User:
    """
    Dependency to get the current user from a WebSocket connection.
    Assumes the session token is passed as a cookie.
    """
    session_cookie = websocket.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Here you would decode your session cookie or JWT to get the user_id.
    payload = decode_access_token(session_cookie)  # This function is a placeholder
    user_id = payload.get("sub") if payload else None  # Assuming 'sub' is the user ID in the token

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user