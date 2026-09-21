"""Audit models."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import relationship

from app.db import Base


class SettingsChangeLog(Base):
    __tablename__ = "settings_change_log"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, server_default=func.now())
    changes = Column(JSON, nullable=False)

    user = relationship("User")
