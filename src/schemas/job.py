from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime


class JobBase(BaseModel):
    title: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "EUR"
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    source_url: str
    source_platform: Optional[str] = None
    external_id: Optional[str] = None
    is_active: bool = True
    posted_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    skills: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    company_id: Optional[int] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    is_active: Optional[bool] = None
    skills: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    company_id: Optional[int] = None


class JobResponse(JobBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    skip: int
    limit: int
