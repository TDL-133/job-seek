from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models import get_db, Company
from ..schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse

router = APIRouter()


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    name: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all companies with optional filters."""
    query = db.query(Company)
    
    if name:
        query = query.filter(Company.name.ilike(f"%{name}%"))
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    
    total = query.count()
    companies = query.offset(skip).limit(limit).all()
    
    return CompanyListResponse(companies=companies, total=total, skip=skip, limit=limit)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get a specific company by ID."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyResponse)
async def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """Create a new company."""
    db_company = Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int, 
    company: CompanyUpdate, 
    db: Session = Depends(get_db)
):
    """Update a company."""
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = company.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company


@router.delete("/{company_id}")
async def delete_company(company_id: int, db: Session = Depends(get_db)):
    """Delete a company."""
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db.delete(db_company)
    db.commit()
    return {"message": "Company deleted successfully"}
