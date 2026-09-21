from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.auth import verify_token
from app.db import AsyncSessionLocal
from sqlalchemy import select
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                payload = verify_token(token)
                username = payload.get("sub")
                if username:
                    # Get user from db
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(User).where(User.username == username))
                        user = result.scalar_one_or_none()
                        if user:
                            request.state.user_id = user.id
                            request.state.org_id = user.organization_id
            except Exception as e:
                logger.warning(f"Token verification failed: {e}")
        
        response = await call_next(request)
        return response