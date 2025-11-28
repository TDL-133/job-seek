from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class CriteriaType(str, enum.Enum):
    JOB_TITLE = "job_title"
    LOCATION = "location"
    CONTRACT_TYPE = "contract_type"
    SALARY = "salary"
    WORK_MODE = "work_mode"
    COMPANY_SIZE = "company_size"
    SENIORITY = "seniority"
    VALUES = "values"
    LANGUAGES = "languages"
    SKILLS = "skills"


class ScoringCriteria(Base):
    __tablename__ = "scoring_criteria"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Criteria type
    criteria_type = Column(String(50), nullable=False)
    
    # Toggle: "Critère à afficher / Non obligatoire"
    enabled = Column(Boolean, default=True)
    
    # Global importance for this criteria (0-100)
    importance = Column(Integer, default=50)
    
    # Sub-criteria with individual importance
    # Structure: {
    #   "options": [{"name": "Remote", "enabled": true, "importance": 80}, ...],
    #   "custom": [{"name": "Python", "importance": 100}, ...],
    #   "value": "Paris",  # For single-value criteria like location
    #   "max_distance": 50  # For location criteria (km)
    #   "min_value": 50000  # For salary criteria
    # }
    sub_criteria = Column(JSON, default=dict)
    
    # Relationship
    user = relationship("User", back_populates="scoring_criteria")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ScoringCriteria(id={self.id}, type='{self.criteria_type}', enabled={self.enabled})>"


# Default criteria configuration
DEFAULT_CRITERIA = [
    {
        "criteria_type": CriteriaType.JOB_TITLE.value,
        "enabled": True,
        "importance": 100,
        "sub_criteria": {"options": [], "custom": []}
    },
    {
        "criteria_type": CriteriaType.LOCATION.value,
        "enabled": True,
        "importance": 80,
        "sub_criteria": {"value": "", "max_distance": 50}
    },
    {
        "criteria_type": CriteriaType.CONTRACT_TYPE.value,
        "enabled": True,
        "importance": 70,
        "sub_criteria": {
            "options": [
                {"name": "CDI", "enabled": True, "importance": 100},
                {"name": "CDD", "enabled": False, "importance": 50},
                {"name": "Freelance", "enabled": False, "importance": 50},
                {"name": "Stage", "enabled": False, "importance": 30},
            ]
        }
    },
    {
        "criteria_type": CriteriaType.SALARY.value,
        "enabled": True,
        "importance": 60,
        "sub_criteria": {"min_value": None, "currency": "EUR"}
    },
    {
        "criteria_type": CriteriaType.WORK_MODE.value,
        "enabled": True,
        "importance": 70,
        "sub_criteria": {
            "options": [
                {"name": "Remote", "enabled": True, "importance": 80},
                {"name": "Hybrid", "enabled": True, "importance": 70},
                {"name": "Onsite", "enabled": True, "importance": 50},
                {"name": "Flexible", "enabled": True, "importance": 90},
            ]
        }
    },
    {
        "criteria_type": CriteriaType.COMPANY_SIZE.value,
        "enabled": False,
        "importance": 40,
        "sub_criteria": {
            "options": [
                {"name": "Startup", "enabled": True, "importance": 70},
                {"name": "Scale-up", "enabled": True, "importance": 80},
                {"name": "PME", "enabled": True, "importance": 60},
                {"name": "Grand groupe", "enabled": True, "importance": 50},
            ]
        }
    },
    {
        "criteria_type": CriteriaType.SENIORITY.value,
        "enabled": True,
        "importance": 60,
        "sub_criteria": {
            "options": [
                {"name": "Junior", "enabled": False, "importance": 50},
                {"name": "Mid", "enabled": True, "importance": 80},
                {"name": "Senior", "enabled": True, "importance": 90},
                {"name": "Lead", "enabled": False, "importance": 70},
            ]
        }
    },
    {
        "criteria_type": CriteriaType.VALUES.value,
        "enabled": False,
        "importance": 50,
        "sub_criteria": {
            "options": [
                {"name": "Impact", "enabled": True, "importance": 70},
                {"name": "Innovation", "enabled": True, "importance": 80},
                {"name": "Bienveillance", "enabled": True, "importance": 60},
                {"name": "Flexibilité", "enabled": True, "importance": 75},
            ],
            "custom": []
        }
    },
    {
        "criteria_type": CriteriaType.LANGUAGES.value,
        "enabled": False,
        "importance": 50,
        "sub_criteria": {"options": [], "custom": []}
    },
    {
        "criteria_type": CriteriaType.SKILLS.value,
        "enabled": True,
        "importance": 80,
        "sub_criteria": {"options": [], "custom": []}
    },
]
