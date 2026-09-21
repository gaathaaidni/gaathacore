from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..db import Base
import datetime

class Asset(Base):
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(String(50))
    value = Column(Float)
    user_id = Column(Integer, ForeignKey('users.id'))
    assigned_to = relationship("User", back_populates="assets")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
