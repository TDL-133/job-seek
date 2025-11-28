from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    requirements = Column(Text)
    
    # Location
    location = Column(String(255))
    remote_type = Column(String(50))  # remote, hybrid, onsite
    
    # Compensation
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String(10), default="EUR")
    
    # Job details
    job_type = Column(String(50))  # full-time, part-time, contract, internship
    experience_level = Column(String(50))  # entry, mid, senior, lead
    
    # Source information
    source_url = Column(String(500), unique=True)
    source_platform = Column(String(50))  # linkedin, indeed, glassdoor, etc.
    external_id = Column(String(255))
    
    # Status
    is_active = Column(Boolean, default=True)
    posted_date = Column(DateTime)
    expires_date = Column(DateTime)
    
    # Metadata
    skills = Column(JSON)  # List of required skills
    benefits = Column(JSON)  # List of benefits
    
    # Relationships
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}')>"
