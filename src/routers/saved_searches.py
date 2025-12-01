"""
Saved searches router - CRUD operations for user's saved search queries.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..models import get_db, User, SavedSearch
from ..services.auth import get_current_user_required


router = APIRouter()


# Pydantic schemas
class SavedSearchCreate(BaseModel):
    name: str
    keywords: str
    location: str


class SavedSearchResponse(BaseModel):
    id: int
    name: str
    keywords: str
    location: str
    created_at: Optional[datetime]
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class SavedSearchListResponse(BaseModel):
    searches: List[SavedSearchResponse]
    total: int


@router.get("/", response_model=SavedSearchListResponse)
async def list_saved_searches(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """List all saved searches for the current user, sorted by last used."""
    searches = db.query(SavedSearch).filter(
        SavedSearch.user_id == user.id
    ).order_by(desc(SavedSearch.last_used_at)).all()
    
    return SavedSearchListResponse(
        searches=searches,
        total=len(searches)
    )


@router.post("/", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    data: SavedSearchCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Save a new search query."""
    # Check for duplicates (same keywords + location)
    existing = db.query(SavedSearch).filter(
        SavedSearch.user_id == user.id,
        SavedSearch.keywords == data.keywords,
        SavedSearch.location == data.location
    ).first()
    
    if existing:
        # Update the existing one instead of creating duplicate
        existing.name = data.name
        existing.last_used_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new saved search
    saved_search = SavedSearch(
        user_id=user.id,
        name=data.name,
        keywords=data.keywords,
        location=data.location
    )
    
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    
    return saved_search


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Delete a saved search."""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user.id
    ).first()
    
    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    db.delete(saved_search)
    db.commit()
    
    return None


@router.put("/{search_id}/use", response_model=SavedSearchResponse)
async def mark_search_used(
    search_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Mark a saved search as recently used (updates last_used_at)."""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user.id
    ).first()
    
    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    saved_search.last_used_at = datetime.utcnow()
    db.commit()
    db.refresh(saved_search)
    
    return saved_search
