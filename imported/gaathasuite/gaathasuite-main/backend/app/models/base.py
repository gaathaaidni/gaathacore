"""
This module re-exports the Base from app.db to ensure a single Base class
for all models to use. The ActivityLog model is defined here for organizational
purposes but uses the shared Base.
"""
from app.db import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, func, Boolean, String, Text, ForeignKey
from datetime import datetime

class ActivityLog(Base):
    __tablename__ = 'activity_log'

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey('organizations.id'))
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[str] = mapped_column(Text)

__all__ = ['Base', 'ActivityLog']