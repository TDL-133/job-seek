"""
User Scoring Preferences Model for V2 Scoring System

Stores user preferences for the fixed-point scoring system:
- preferred_city
- min_salary
- target_seniority
- priority_skills
- trusted_sources
- attractiveness_keywords
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class UserScoringPreferences(Base):
    """
    User preferences for job scoring.
    One-to-one relationship with User.
    """
    __tablename__ = "user_scoring_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Geography preferences
    preferred_city = Column(String(100), default="")
    
    # Salary preferences (in EUR, annual)
    min_salary = Column(Integer, default=50000)
    
    # Target seniority level: junior, mid, senior, head
    target_seniority = Column(String(20), default="senior")
    
    # Priority skills (in addition to CV skills)
    # Structure: ["Python", "AI/ML", "Product Strategy"]
    priority_skills = Column(JSON, default=list)
    
    # Trusted sources configuration
    # Structure: {"linkedin": true, "indeed": true, "glassdoor": true, "welcometothejungle": true}
    trusted_sources = Column(JSON, default=dict)
    
    # Attractiveness keywords (custom + defaults)
    # Structure: {
    #   "high": ["ai", "climate", ...],
    #   "medium": ["startup", "fintech", ...],
    #   "custom": ["my-keyword"]
    # }
    attractiveness_keywords = Column(JSON, default=dict)
    
    # Relationship
    user = relationship("User", back_populates="scoring_preferences")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<UserScoringPreferences(user_id={self.user_id}, city='{self.preferred_city}')>"
    
    def to_dict(self) -> dict:
        """Convert to dict for scoring service."""
        return {
            "preferred_city": self.preferred_city or "",
            "min_salary": self.min_salary or 50000,
            "target_seniority": self.target_seniority or "senior",
            "priority_skills": self.priority_skills or [],
            "trusted_sources": self.trusted_sources or {},
            "attractiveness_keywords": self.attractiveness_keywords or {},
        }


# Default preferences
DEFAULT_SCORING_PREFERENCES = {
    "preferred_city": "",
    "min_salary": 50000,
    "target_seniority": "senior",
    "priority_skills": [],
    "trusted_sources": {
        "linkedin": True,
        "indeed": True,
        "glassdoor": True,
        "welcometothejungle": True,
    },
    "attractiveness_keywords": {
        "high": [
            "ai", "artificial intelligence", "machine learning", "ml",
            "climate", "sustainability", "impact", "mission-driven",
            "healthtech", "medtech", "biotech", "greentech",
            "series b", "series c", "unicorn",
        ],
        "medium": [
            "series a", "startup", "scale-up", "scaleup",
            "fintech", "edtech", "proptech",
            "fast-growing", "hypergrowth", "high-growth",
            "innovative", "disruptive",
        ],
        "custom": [],
    }
}
