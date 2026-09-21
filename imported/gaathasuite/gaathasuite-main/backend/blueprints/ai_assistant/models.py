"""Models used by the AI assistant blueprint."""

from app.db import Base
from app.models.user import User

from sqlalchemy import Column, ForeignKey, Integer, String


class AIAssistantEmployee(Base):
    """Employee record for the AI assistant HR endpoints.

    The class intentionally does not use the generic name ``Employee`` because
    the main application already has ``app.models.hr.Employee`` registered on
    the same SQLAlchemy declarative base. Registering two ORM classes with the
    same class name makes SQLAlchemy string relationships such as
    ``relationship('Employee')`` ambiguous during mapper configuration.
    """

    __tablename__ = "hr_employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    position = Column(String)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)


# Preserve the existing module API used by routes.py while keeping the ORM
# registry key unique (``AIAssistantEmployee`` instead of ``Employee``).
Employee = AIAssistantEmployee

__all__ = [
    "AIAssistantEmployee", "Employee", "User"
]
