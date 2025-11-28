from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PreferenceBase(BaseModel):
    target_titles: Optional[List[str]] = None
    target_keywords: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    remote_preference: Optional[str] = "any"
    willing_to_relocate: bool = False
    min_salary: Optional[float] = None
    preferred_currency: str = "EUR"
    preferred_company_sizes: Optional[List[str]] = None
    preferred_industries: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    experience_years: Optional[int] = None
    skills: Optional[List[str]] = None
    search_frequency: str = "daily"
    email_alerts: bool = True


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceUpdate(PreferenceBase):
    pass


class PreferenceResponse(PreferenceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
