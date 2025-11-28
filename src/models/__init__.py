from .base import Base, engine, SessionLocal, get_db
from .job import Job
from .company import Company
from .application import Application, ApplicationStatus
from .user_preference import UserPreference
from .user import User
from .user_profile import UserProfile
from .scoring_criteria import ScoringCriteria, CriteriaType, DEFAULT_CRITERIA
from .scoring_preferences import UserScoringPreferences, DEFAULT_SCORING_PREFERENCES
from .blacklist import Blacklist
from .email_alert import EmailAlert

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "Job",
    "Company",
    "Application",
    "ApplicationStatus",
    "UserPreference",
    "User",
    "UserProfile",
    "ScoringCriteria",
    "CriteriaType",
    "DEFAULT_CRITERIA",
    "UserScoringPreferences",
    "DEFAULT_SCORING_PREFERENCES",
    "Blacklist",
    "EmailAlert",
]
