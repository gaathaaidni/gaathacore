from celery import shared_task
from app.db import AsyncSessionLocal
from app.models.procurement import Vendor
from sqlalchemy import select
from datetime import datetime, timedelta
from email.message import EmailMessage
import secrets
import asyncio
import os
import smtplib
import logging

logger = logging.getLogger(__name__)

@shared_task
def refresh_expired_vendors():
    """Background task to regenerate portal tokens for all expired vendors."""
    return asyncio.run(_do_refresh())

async def _do_refresh():
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        stmt = select(Vendor).where(Vendor.expires_at < now)
        result = await db.execute(stmt)
        expired_vendors = result.scalars().all()
        
        count = 0
        for vendor in expired_vendors:
            vendor.portal_token = secrets.token_hex(16)
            vendor.expires_at = now + timedelta(days=7)
            notification_sent = send_vendor_notification(vendor.email, vendor.portal_token)
            if not notification_sent:
                logger.warning("Vendor portal token refreshed but email notification was not sent: %s", vendor.email)
            count += 1
        
        if count > 0:
            await db.commit()
            return f"Successfully refreshed {count} vendor tokens."
        return "No expired tokens found."


def send_vendor_notification(email: str, portal_token: str) -> bool:
    """Send a vendor portal token notification via SMTP when configured."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"true", "1", "yes"}
    sender_email = os.getenv("SMTP_FROM_EMAIL", "noreply@example.com")

    if not smtp_host or not smtp_user or not smtp_password:
        logger.info("SMTP configuration is not complete; vendor notification skipped for %s", email)
        return False

    message = EmailMessage()
    message["Subject"] = "Your vendor portal access has been refreshed"
    message["From"] = sender_email
    message["To"] = email
    message.set_content(
        f"Your vendor portal access token has been refreshed.\n\n"
        f"Portal Token: {portal_token}\n"
        "Please use this token to sign in to the vendor portal and update your profile.\n"
        "If you did not request this, please contact support.\n"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
            if smtp_use_tls:
                smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
        logger.info("Vendor notification email sent to %s", email)
        return True
    except Exception as exc:
        logger.error("Failed to send vendor notification email to %s: %s", email, exc)
        return False