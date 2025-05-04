from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10, 2))
    description = Column(String(500))
    reference_id = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="transactions")
    organization = relationship("Organization", back_populates="transactions")
