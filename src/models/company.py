from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Company info
    website = Column(String(500))
    linkedin_url = Column(String(500))
    logo_url = Column(String(500))
    
    # Location
    headquarters = Column(String(255))
    locations = Column(JSON)  # List of office locations
    
    # Company details
    industry = Column(String(100))
    company_size = Column(String(50))  # 1-10, 11-50, 51-200, etc.
    founded_year = Column(Integer)
    
    # Ratings (from Glassdoor, etc.)
    rating = Column(Float)
    reviews_count = Column(Integer)
    
    # Social/Culture
    culture_keywords = Column(JSON)  # tech stack, values, etc.
    
    # Relationships
    jobs = relationship("Job", back_populates="company")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"
