from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..models import get_db, User, Blacklist, Company
from ..services.auth import get_current_user_required

router = APIRouter()


# Schemas
class BlacklistCreate(BaseModel):
    company_name: str
    company_id: Optional[int] = None
    reason: Optional[str] = None


class BlacklistResponse(BaseModel):
    id: int
    company_name: str
    company_id: Optional[int] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BlacklistListResponse(BaseModel):
    items: List[BlacklistResponse]
    total: int


@router.get("/", response_model=BlacklistListResponse)
async def get_blacklist(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Get all blacklisted companies for the user.
    
    Step 10 from PRD: Display blacklist page.
    """
    items = db.query(Blacklist).filter(
        Blacklist.user_id == user.id
    ).order_by(Blacklist.created_at.desc()).all()
    
    return BlacklistListResponse(
        items=items,
        total=len(items)
    )


@router.post("/", response_model=BlacklistResponse)
async def add_to_blacklist(
    data: BlacklistCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Add a company to the blacklist.
    
    Step 8 from PRD: "Ajouter à la blacklist" button on job dashboard.
    """
    # Check if already blacklisted
    existing = db.query(Blacklist).filter(
        Blacklist.user_id == user.id,
        Blacklist.company_name.ilike(data.company_name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Company '{data.company_name}' is already blacklisted"
        )
    
    # If company_id provided, verify it exists
    if data.company_id:
        company = db.query(Company).filter(Company.id == data.company_id).first()
        if not company:
            data.company_id = None
    
    blacklist_entry = Blacklist(
        user_id=user.id,
        company_name=data.company_name,
        company_id=data.company_id,
        reason=data.reason
    )
    
    db.add(blacklist_entry)
    db.commit()
    db.refresh(blacklist_entry)
    
    return blacklist_entry


@router.delete("/{blacklist_id}")
async def remove_from_blacklist(
    blacklist_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Remove a company from the blacklist.
    
    Step 10 from PRD: Allow removing companies from blacklist.
    """
    entry = db.query(Blacklist).filter(
        Blacklist.id == blacklist_id,
        Blacklist.user_id == user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    
    company_name = entry.company_name
    db.delete(entry)
    db.commit()
    
    return {"message": f"Company '{company_name}' removed from blacklist"}


@router.get("/check/{company_name}")
async def check_blacklist(
    company_name: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Check if a company is blacklisted."""
    entry = db.query(Blacklist).filter(
        Blacklist.user_id == user.id,
        Blacklist.company_name.ilike(company_name)
    ).first()
    
    return {
        "company_name": company_name,
        "is_blacklisted": entry is not None,
        "reason": entry.reason if entry else None
    }
