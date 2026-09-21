from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..db import Base
import datetime

class Coupon(Base):
    __tablename__ = 'coupons'

    id = Column(Integer, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    discount_type = Column(String(20), nullable=False, default='percentage')  # 'percentage' or 'fixed'
    value = Column(Float, nullable=False, default=0.0)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    usage_limit = Column(Integer, default=1)
    used_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Coupon {self.code}>'