from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class EmailAlert(Base):
    __tablename__ = "email_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Alert settings
    enabled = Column(Boolean, default=True)
    frequency = Column(String(20), default="daily")  # daily, weekly
    send_time = Column(String(5), default="09:00")  # HH:MM format
    
    # Snapshot of criteria at time of alert creation
    criteria_snapshot = Column(JSON)
    
    # Tracking
    last_sent_at = Column(DateTime(timezone=True))
    jobs_sent_count = Column(Integer, default=0)
    
    # Relationship
    user = relationship("User", back_populates="email_alert")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<EmailAlert(id={self.id}, user_id={self.user_id}, enabled={self.enabled})>"
