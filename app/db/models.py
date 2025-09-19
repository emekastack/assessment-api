from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.database import Base

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sent_requests = relationship("PartnerRequest", foreign_keys="PartnerRequest.sender_id", back_populates="sender")
    received_requests = relationship("PartnerRequest", foreign_keys="PartnerRequest.recipient_id", back_populates="recipient")
    partnerships_a = relationship("Partnership", foreign_keys="Partnership.user_a_id", back_populates="user_a")
    partnerships_b = relationship("Partnership", foreign_keys="Partnership.user_b_id", back_populates="user_b")

class PartnerRequest(Base):
    __tablename__ = "partner_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_requests")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_requests")

class Partnership(Base):
    __tablename__ = "partnerships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_a = relationship("User", foreign_keys=[user_a_id], back_populates="partnerships_a")
    user_b = relationship("User", foreign_keys=[user_b_id], back_populates="partnerships_b")
