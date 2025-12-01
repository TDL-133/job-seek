from pydantic import BaseModel, field_validator
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum


class ApplicationStatusEnum(str, Enum):
    SAVED = "SAVED"
    APPLIED = "APPLIED"
    PHONE_SCREEN = "PHONE_SCREEN"
    INTERVIEW = "INTERVIEW"
    TECHNICAL = "TECHNICAL"
    FINAL_ROUND = "FINAL_ROUND"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class ApplicationBase(BaseModel):
    job_id: int
    status: ApplicationStatusEnum = ApplicationStatusEnum.SAVED
    cover_letter: Optional[str] = None
    resume_version: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    interview_type: Optional[str] = None
    interview_notes: Optional[str] = None
    offer_amount: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatusEnum] = None
    cover_letter: Optional[str] = None
    resume_version: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    interview_type: Optional[str] = None
    interview_notes: Optional[str] = None
    offer_amount: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApplicationResponse(ApplicationBase):
    id: int
    applied_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    applications: List[ApplicationResponse]
    total: int
    skip: int
    limit: int


class JobSummary(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    posted_date: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_validator('company', mode='before')
    @classmethod
    def extract_company_name(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        # If it's a Company object, extract the name
        if hasattr(v, 'name'):
            return v.name
        return str(v)


class ApplicationWithJobResponse(ApplicationResponse):
    job: Optional[JobSummary] = None


class ApplicationWithJobListResponse(BaseModel):
    applications: List[ApplicationWithJobResponse]
    total: int
    skip: int
    limit: int
