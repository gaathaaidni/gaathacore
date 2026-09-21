from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from app.models.base import Base

class Customer(Base):
    __tablename__ = 'customers'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default='USD')
    company: Mapped[str] = mapped_column(String(255), nullable=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.id'), nullable=True)

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="customer")

class Lead(Base):
    __tablename__ = 'leads'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    company: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='new')

class Opportunity(Base):
    __tablename__ = 'opportunities'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'))
    value: Mapped[float] = mapped_column(default=0.0)
    stage: Mapped[str] = mapped_column(String(100), default='prospect')
    
    customer: Mapped["Customer"] = relationship()