import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.config import Config
from app.utils.dependencies import get_db
from app.models.user import User
from app.utils.signing import generate_token, verify_token
from app.tasks import celery
from app.utils.email import _send_email_sync
# Assuming a password hashing utility exists
# from app.utils.security import get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])


@celery.task(name="tasks.send_password_reset_email")
def send_password_reset_email(user_id: int, email: str):
    reset_token = generate_token({"user_id": user_id, "action": "password_reset"})
    reset_url = Config.public_url(f"/auth/reset-password?token={reset_token}")
    _send_email_sync(
        to_email=email,
        subject="Gaatha Suite: Password Reset Request",
        body=f"Hello,\n\nYou requested a password reset. Click the link below to set a new password:\n{reset_url}\n\nThis link expires in 1 hour.",
    )

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@router.post("/password-reset-request")
async def request_password_reset(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """
    Initiates the password reset flow.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if user:
        send_password_reset_email.delay(user.id, user.email)
    
    # Always return success to prevent email enumeration
    return {"message": "If an account exists with that email, a reset link has been sent."}

@router.post("/password-reset-confirm")
async def confirm_password_reset(data: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """
    Verifies the token and updates the user's password.
    """
    payload = verify_token(data.token, max_age=3600) # 1 hour expiry
    if not payload or payload.get("action") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid or expired token.")
    
    user_id = payload.get("user_id")
    user = await db.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user.set_password(data.new_password)
    
    await db.commit()
    return {"message": "Password updated successfully."}