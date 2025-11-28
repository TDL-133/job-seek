from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class ApplicationStatus(enum.Enum):
    SAVED = "saved"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    FINAL_ROUND = "final_round"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Status tracking
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.SAVED)
    
    # Application details
    cover_letter = Column(Text)
    resume_version = Column(String(255))  # Which resume version used
    
    # Contact info
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    
    # Notes and follow-up
    notes = Column(Text)
    next_action = Column(String(255))
    next_action_date = Column(DateTime)
    
    # Interview tracking
    interview_date = Column(DateTime)
    interview_type = Column(String(50))  # video, phone, onsite
    interview_notes = Column(Text)
    
    # Outcome
    offer_amount = Column(String(100))
    rejection_reason = Column(Text)
    
    # Relationships
    job_id = Column(Integer, ForeignKey("jobs.id"))
    job = relationship("Job", back_populates="applications")
    
    # Timestamps
    applied_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Application(id={self.id}, status='{self.status}')>"
