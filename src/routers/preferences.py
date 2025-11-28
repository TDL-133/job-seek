from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models import get_db, UserPreference
from ..schemas.preference import PreferenceCreate, PreferenceUpdate, PreferenceResponse

router = APIRouter()


@router.get("/", response_model=PreferenceResponse)
async def get_preferences(db: Session = Depends(get_db)):
    """Get user preferences (creates default if none exists)."""
    preference = db.query(UserPreference).first()
    
    if not preference:
        # Create default preferences
        preference = UserPreference()
        db.add(preference)
        db.commit()
        db.refresh(preference)
    
    return preference


@router.put("/", response_model=PreferenceResponse)
async def update_preferences(
    preferences: PreferenceUpdate, 
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    db_preference = db.query(UserPreference).first()
    
    if not db_preference:
        db_preference = UserPreference()
        db.add(db_preference)
    
    update_data = preferences.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_preference, field, value)
    
    db.commit()
    db.refresh(db_preference)
    return db_preference


@router.post("/reset", response_model=PreferenceResponse)
async def reset_preferences(db: Session = Depends(get_db)):
    """Reset preferences to defaults."""
    db_preference = db.query(UserPreference).first()
    
    if db_preference:
        db.delete(db_preference)
    
    new_preference = UserPreference()
    db.add(new_preference)
    db.commit()
    db.refresh(new_preference)
    
    return new_preference
