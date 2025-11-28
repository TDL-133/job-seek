from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None
    headquarters: Optional[str] = None
    locations: Optional[List[str]] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    culture_keywords: Optional[List[str]] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None
    headquarters: Optional[str] = None
    locations: Optional[List[str]] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    culture_keywords: Optional[List[str]] = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int
    skip: int
    limit: int
