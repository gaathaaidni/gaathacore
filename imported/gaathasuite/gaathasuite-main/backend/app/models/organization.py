"""Organization model."""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    func,
    JSON,
)

from app.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    description = Column(String(500))
    logo_url = Column(String(500))
    website = Column(String(200))
    email = Column(String(120))
    address = Column(String(255))
    phone = Column(String(50))
    currency = Column(String(10), default="USD")
    tax_id = Column(String(100))
    invoice_notes = Column(String)
    invoice_terms = Column(String)
    invoice_template = Column(String(50), default="classic")
    industry = Column(String(100), nullable=True)
    custom_fields = Column(JSON)
    company_size = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())