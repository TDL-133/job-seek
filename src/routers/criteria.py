from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models import (
    get_db, User, ScoringCriteria, DEFAULT_CRITERIA, CriteriaType,
    UserScoringPreferences, DEFAULT_SCORING_PREFERENCES
)
from ..services.auth import get_current_user_required

router = APIRouter()


# Schemas
class SubCriteriaOption(BaseModel):
    name: str
    enabled: bool = True
    importance: int = 50  # 0-100


class SubCriteriaConfig(BaseModel):
    options: Optional[List[SubCriteriaOption]] = None
    custom: Optional[List[SubCriteriaOption]] = None
    value: Optional[str] = None
    max_distance: Optional[int] = None
    min_value: Optional[float] = None
    currency: Optional[str] = None


class CriteriaResponse(BaseModel):
    id: int
    criteria_type: str
    enabled: bool
    importance: int
    sub_criteria: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CriteriaUpdate(BaseModel):
    enabled: Optional[bool] = None
    importance: Optional[int] = None
    sub_criteria: Optional[Dict[str, Any]] = None


class CriteriaListResponse(BaseModel):
    criteria: List[CriteriaResponse]
    total: int


class AddSubCriteriaRequest(BaseModel):
    name: str
    importance: int = 50


@router.get("/", response_model=CriteriaListResponse)
async def get_all_criteria(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Get all scoring criteria for the user.
    
    Step 6 from PRD: Display criteria configuration cards.
    """
    criteria_list = db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id
    ).all()
    
    # Initialize defaults if no criteria exist
    if not criteria_list:
        for criteria_config in DEFAULT_CRITERIA:
            criteria = ScoringCriteria(
                user_id=user.id,
                **criteria_config
            )
            db.add(criteria)
        db.commit()
        
        criteria_list = db.query(ScoringCriteria).filter(
            ScoringCriteria.user_id == user.id
        ).all()
    
    return CriteriaListResponse(
        criteria=criteria_list,
        total=len(criteria_list)
    )


@router.get("/{criteria_type}", response_model=CriteriaResponse)
async def get_criteria(
    criteria_type: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get a specific criteria by type."""
    criteria = db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id,
        ScoringCriteria.criteria_type == criteria_type
    ).first()
    
    if not criteria:
        raise HTTPException(status_code=404, detail=f"Criteria '{criteria_type}' not found")
    
    return criteria


@router.put("/{criteria_type}", response_model=CriteriaResponse)
async def update_criteria(
    criteria_type: str,
    update_data: CriteriaUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Update a specific criteria.
    
    Step 6 from PRD: Toggle enabled, adjust importance (0-100), modify sub-criteria.
    """
    criteria = db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id,
        ScoringCriteria.criteria_type == criteria_type
    ).first()
    
    if not criteria:
        raise HTTPException(status_code=404, detail=f"Criteria '{criteria_type}' not found")
    
    # Validate importance range
    if update_data.importance is not None:
        if not 0 <= update_data.importance <= 100:
            raise HTTPException(
                status_code=400, 
                detail="Importance must be between 0 and 100"
            )
    
    # Update fields
    if update_data.enabled is not None:
        criteria.enabled = update_data.enabled
    
    if update_data.importance is not None:
        criteria.importance = update_data.importance
    
    if update_data.sub_criteria is not None:
        criteria.sub_criteria = update_data.sub_criteria
    
    db.commit()
    db.refresh(criteria)
    
    return criteria


@router.put("/", response_model=CriteriaListResponse)
async def update_all_criteria(
    updates: List[Dict[str, Any]],
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Batch update multiple criteria at once.
    
    Useful for "Lancer ma recherche" button - save all criteria at once.
    """
    updated_criteria = []
    
    for update in updates:
        criteria_type = update.get("criteria_type")
        if not criteria_type:
            continue
        
        criteria = db.query(ScoringCriteria).filter(
            ScoringCriteria.user_id == user.id,
            ScoringCriteria.criteria_type == criteria_type
        ).first()
        
        if not criteria:
            continue
        
        if "enabled" in update:
            criteria.enabled = update["enabled"]
        
        if "importance" in update:
            importance = update["importance"]
            if 0 <= importance <= 100:
                criteria.importance = importance
        
        if "sub_criteria" in update:
            criteria.sub_criteria = update["sub_criteria"]
        
        updated_criteria.append(criteria)
    
    db.commit()
    
    # Refresh all
    for criteria in updated_criteria:
        db.refresh(criteria)
    
    # Return all criteria
    all_criteria = db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id
    ).all()
    
    return CriteriaListResponse(
        criteria=all_criteria,
        total=len(all_criteria)
    )


@router.post("/{criteria_type}/sub", response_model=CriteriaResponse)
async def add_sub_criteria(
    criteria_type: str,
    sub_item: AddSubCriteriaRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Add a custom sub-criterion to a criteria.
    
    Step 6 from PRD: "+ Ajouter un sous-critère" button.
    """
    criteria = db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id,
        ScoringCriteria.criteria_type == criteria_type
    ).first()
    
    if not criteria:
        raise HTTPException(status_code=404, detail=f"Criteria '{criteria_type}' not found")
    
    # Validate importance
    if not 0 <= sub_item.importance <= 100:
        raise HTTPException(
            status_code=400,
            detail="Importance must be between 0 and 100"
        )
    
    # Get current sub_criteria
    sub_criteria = criteria.sub_criteria or {}
    
    # Add to custom list
    custom_list = sub_criteria.get("custom", [])
    
    # Check if already exists
    for item in custom_list:
        if item.get("name", "").lower() == sub_item.name.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Sub-criterion '{sub_item.name}' already exists"
            )
    
    custom_list.append({
        "name": sub_item.name,
        "enabled": True,
        "importance": sub_item.importance
    })
    
    sub_criteria["custom"] = custom_list
    criteria.sub_criteria = sub_criteria
    
    db.commit()
    db.refresh(criteria)
    
    return criteria


@router.delete("/{criteria_type}/sub/{sub_name}", response_model=CriteriaResponse)
async def remove_sub_criteria(
    criteria_type: str,
    sub_name: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Remove a custom sub-criterion."""
    criteria = db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id,
        ScoringCriteria.criteria_type == criteria_type
    ).first()
    
    if not criteria:
        raise HTTPException(status_code=404, detail=f"Criteria '{criteria_type}' not found")
    
    sub_criteria = criteria.sub_criteria or {}
    custom_list = sub_criteria.get("custom", [])
    
    # Find and remove
    new_custom = [item for item in custom_list if item.get("name", "").lower() != sub_name.lower()]
    
    if len(new_custom) == len(custom_list):
        raise HTTPException(
            status_code=404,
            detail=f"Sub-criterion '{sub_name}' not found"
        )
    
    sub_criteria["custom"] = new_custom
    criteria.sub_criteria = sub_criteria
    
    db.commit()
    db.refresh(criteria)
    
    return criteria


@router.post("/reset")
async def reset_criteria(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Reset all criteria to defaults."""
    # Delete existing criteria
    db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id
    ).delete()
    
    # Create defaults
    for criteria_config in DEFAULT_CRITERIA:
        criteria = ScoringCriteria(
            user_id=user.id,
            **criteria_config
        )
        db.add(criteria)
    
    db.commit()
    
    return {"message": "Criteria reset to defaults"}


# ============================================================================
# V2 Scoring Preferences Endpoints
# ============================================================================

class ScoringPreferencesResponse(BaseModel):
    """Response model for scoring preferences."""
    id: int
    preferred_city: str = ""
    min_salary: int = 50000
    target_seniority: str = "senior"
    priority_skills: List[str] = []
    trusted_sources: Dict[str, bool] = {}
    attractiveness_keywords: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScoringPreferencesUpdate(BaseModel):
    """Request model for updating scoring preferences."""
    preferred_city: Optional[str] = None
    min_salary: Optional[int] = Field(None, ge=0, le=500000)
    target_seniority: Optional[str] = Field(None, pattern="^(junior|mid|senior|head)$")
    priority_skills: Optional[List[str]] = None
    trusted_sources: Optional[Dict[str, bool]] = None
    attractiveness_keywords: Optional[Dict[str, Any]] = None


class SourceTrustUpdate(BaseModel):
    """Request model for toggling source trust."""
    trusted: bool


@router.get("/preferences/v2", response_model=ScoringPreferencesResponse)
async def get_scoring_preferences(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Get user's V2 scoring preferences.
    
    Creates default preferences if none exist.
    """
    prefs = db.query(UserScoringPreferences).filter(
        UserScoringPreferences.user_id == user.id
    ).first()
    
    # Create defaults if not exists
    if not prefs:
        prefs = UserScoringPreferences(
            user_id=user.id,
            **DEFAULT_SCORING_PREFERENCES
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs


@router.put("/preferences/v2", response_model=ScoringPreferencesResponse)
async def update_scoring_preferences(
    update_data: ScoringPreferencesUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Update user's V2 scoring preferences.
    
    Only provided fields are updated.
    """
    prefs = db.query(UserScoringPreferences).filter(
        UserScoringPreferences.user_id == user.id
    ).first()
    
    # Create if not exists
    if not prefs:
        prefs = UserScoringPreferences(
            user_id=user.id,
            **DEFAULT_SCORING_PREFERENCES
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    # Update provided fields
    if update_data.preferred_city is not None:
        prefs.preferred_city = update_data.preferred_city
    
    if update_data.min_salary is not None:
        prefs.min_salary = update_data.min_salary
    
    if update_data.target_seniority is not None:
        prefs.target_seniority = update_data.target_seniority
    
    if update_data.priority_skills is not None:
        prefs.priority_skills = update_data.priority_skills
    
    if update_data.trusted_sources is not None:
        # Merge with existing sources
        current_sources = prefs.trusted_sources or {}
        current_sources.update(update_data.trusted_sources)
        prefs.trusted_sources = current_sources
    
    if update_data.attractiveness_keywords is not None:
        prefs.attractiveness_keywords = update_data.attractiveness_keywords
    
    db.commit()
    db.refresh(prefs)
    
    return prefs


@router.put("/preferences/v2/sources/{source}", response_model=ScoringPreferencesResponse)
async def toggle_source_trust(
    source: str,
    update_data: SourceTrustUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Toggle trust status for a specific job source.
    
    Args:
        source: Source name (linkedin, indeed, glassdoor, welcometothejungle)
        update_data: {"trusted": true/false}
    """
    prefs = db.query(UserScoringPreferences).filter(
        UserScoringPreferences.user_id == user.id
    ).first()
    
    if not prefs:
        prefs = UserScoringPreferences(
            user_id=user.id,
            **DEFAULT_SCORING_PREFERENCES
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    # Update source trust
    trusted_sources = prefs.trusted_sources or {}
    trusted_sources[source.lower()] = update_data.trusted
    prefs.trusted_sources = trusted_sources
    
    db.commit()
    db.refresh(prefs)
    
    return prefs


@router.post("/preferences/v2/skills", response_model=ScoringPreferencesResponse)
async def add_priority_skill(
    skill: AddSubCriteriaRequest,  # Reuse existing schema
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Add a priority skill to the list.
    """
    prefs = db.query(UserScoringPreferences).filter(
        UserScoringPreferences.user_id == user.id
    ).first()
    
    if not prefs:
        prefs = UserScoringPreferences(
            user_id=user.id,
            **DEFAULT_SCORING_PREFERENCES
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    # Add skill if not already present
    skills = list(prefs.priority_skills or [])
    skill_lower = skill.name.lower().strip()
    
    if skill_lower not in [s.lower() for s in skills]:
        skills.append(skill.name.strip())
        prefs.priority_skills = skills
        db.commit()
        db.refresh(prefs)
    
    return prefs


@router.delete("/preferences/v2/skills/{skill_name}", response_model=ScoringPreferencesResponse)
async def remove_priority_skill(
    skill_name: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Remove a priority skill from the list.
    """
    prefs = db.query(UserScoringPreferences).filter(
        UserScoringPreferences.user_id == user.id
    ).first()
    
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    skills = list(prefs.priority_skills or [])
    skill_lower = skill_name.lower().strip()
    
    new_skills = [s for s in skills if s.lower() != skill_lower]
    
    if len(new_skills) == len(skills):
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    
    prefs.priority_skills = new_skills
    db.commit()
    db.refresh(prefs)
    
    return prefs


@router.post("/preferences/v2/reset", response_model=ScoringPreferencesResponse)
async def reset_scoring_preferences(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Reset V2 scoring preferences to defaults.
    """
    # Delete existing
    db.query(UserScoringPreferences).filter(
        UserScoringPreferences.user_id == user.id
    ).delete()
    
    # Create new with defaults
    prefs = UserScoringPreferences(
        user_id=user.id,
        **DEFAULT_SCORING_PREFERENCES
    )
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    
    return prefs
