from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # CV data
    cv_file_path = Column(String(500))  # Path to uploaded CV file
    cv_raw_text = Column(Text)  # Extracted text from CV
    user_description = Column(Text)  # User's free-text description
    
    # AI-generated description (from CV + user input)
    ai_description = Column(Text)
    
    # Extracted structured data (from CV analysis)
    experiences = Column(JSON)  # List of {poste, entreprise, dates, lieu, competences}
    skills = Column(JSON)  # List of skills
    languages = Column(JSON)  # List of {language, level}
    education = Column(JSON)  # List of {diplome, ecole, annee}
    
    # Profile summary
    latest_job_title = Column(String(255))
    years_of_experience = Column(Integer)
    preferred_location = Column(String(255))
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cv_analyzed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"
