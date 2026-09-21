from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

class NotificationPreference(Base):
    __tablename__ = 'notification_preferences'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    digest_enabled = Column(Boolean, default=False)