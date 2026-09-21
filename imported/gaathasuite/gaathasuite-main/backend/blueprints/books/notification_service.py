import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.roles import ROLE_ORGADMIN

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def send_settings_change_email(db: AsyncSession, org_id: int, changed_by: User, changes: dict):
        """
        Sends an email notification to organization admins about settings changes.
        In a real application, this would use a proper email sending library (e.g., with Celery for background tasks).
        """
        stmt = select(User).where(User.organization_id == org_id, User.role == ROLE_ORGADMIN)
        result = await db.execute(stmt)
        admins = result.scalars().all()
        
        if not admins:
            logger.warning(f"No org admins found for organization {org_id} to notify of settings change.")
            return

        subject = f"Organization Settings Updated in Gaatha Suite"
        change_details = "\n".join([f"- {key}: changed" for key in changes.keys()])
        body = f"Hello,\n\nThe settings for your organization have been updated by {changed_by.email}.\n\nChanges:\n{change_details}\n\n- The Gaatha Suite Team"
        
        for admin in admins:
            # This is a placeholder for a real email sending service
            logger.info(f"EMAIL_SENT to {admin.email}: Subject: {subject}\nBody: {body}")