"""
Email utility module for sending emails asynchronously.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import Config
import logging

logger = logging.getLogger(__name__)


async def send_email_async(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send email asynchronously.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Run the email sending in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            _send_email_sync,
            to_email,
            subject,
            html_body
        )
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def _send_email_sync(to_email: str, subject: str, html_body: str) -> bool:
    """
    Synchronous email sending function.
    Uses environment variables: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL
    """
    try:
        # Get SMTP config from environment or Config
        smtp_host = getattr(Config, 'SMTP_HOST', 'localhost')
        smtp_port = getattr(Config, 'SMTP_PORT', 587)
        smtp_user = getattr(Config, 'SMTP_USER', '')
        smtp_password = getattr(Config, 'SMTP_PASSWORD', '')
        from_email = getattr(Config, 'SMTP_FROM_EMAIL', 'noreply@gaatha.com')
        
        # For development, if no SMTP config, just log
        if not smtp_host or smtp_host == 'localhost':
            logger.info(f"[DEV MODE] Would send email to {to_email} - Subject: {subject}")
            return True
        
        # Create MIME message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = from_email
        message["To"] = to_email
        
        # Create plain text and HTML versions
        text_body = subject  # Simple text fallback
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        
        message.attach(part1)
        message.attach(part2)
        
        # Connect and send
        if smtp_port == 465:  # SSL
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:  # TLS
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.starttls()
        
        if smtp_user:
            server.login(smtp_user, smtp_password)
        
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False
