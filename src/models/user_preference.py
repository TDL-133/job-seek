from sqlalchemy import Column, Integer, String, JSON, Float, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    
    # Job preferences
    target_titles = Column(JSON)  # List of target job titles
    target_keywords = Column(JSON)  # Keywords to search for
    excluded_keywords = Column(JSON)  # Keywords to exclude
    
    # Location preferences
    preferred_locations = Column(JSON)  # List of preferred locations
    remote_preference = Column(String(50))  # remote, hybrid, onsite, any
    willing_to_relocate = Column(Boolean, default=False)
    
    # Compensation
    min_salary = Column(Float)
    preferred_currency = Column(String(10), default="EUR")
    
    # Company preferences
    preferred_company_sizes = Column(JSON)  # startup, medium, large, enterprise
    preferred_industries = Column(JSON)
    excluded_companies = Column(JSON)  # Companies to avoid
    
    # Experience and skills
    experience_years = Column(Integer)
    skills = Column(JSON)  # User's skills
    
    # Search settings
    search_frequency = Column(String(50), default="daily")  # daily, weekly
    email_alerts = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<UserPreference(id={self.id})>"
