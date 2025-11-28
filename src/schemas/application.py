from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ApplicationStatusEnum(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    FINAL_ROUND = "final_round"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


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
