from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from ..models import get_db, User, UserProfile, ScoringCriteria, DEFAULT_CRITERIA
from ..services.auth import get_current_user_required
from ..services.cv_analysis import CVAnalysisService

router = APIRouter()

# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads/cv")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Schemas
class ExperienceItem(BaseModel):
    poste: str
    entreprise: str
    dates: str
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    lieu: Optional[str] = None
    competences: List[str] = []
    description: Optional[str] = None


class EducationItem(BaseModel):
    diplome: str
    ecole: str
    annee: Optional[str] = None
    lieu: Optional[str] = None


class LanguageItem(BaseModel):
    language: str
    level: str


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    cv_file_path: Optional[str] = None
    user_description: Optional[str] = None
    ai_description: Optional[str] = None
    experiences: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[Dict[str, str]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    latest_job_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    preferred_location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cv_analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    user_description: Optional[str] = None
    ai_description: Optional[str] = None
    experiences: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[Dict[str, str]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    latest_job_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    preferred_location: Optional[str] = None


class CVUploadResponse(BaseModel):
    message: str
    profile: ProfileResponse
    analysis_complete: bool


@router.get("/", response_model=Optional[ProfileResponse])
async def get_profile(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get current user's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    if not profile:
        return None
    
    return profile


@router.post("/upload-cv", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    user_description: Optional[str] = Form(None),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Upload CV file and analyze it.
    
    Step 4.1 from PRD: Upload CV + optional description.
    Returns extracted data for validation.
    """
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Save file
    filename = f"{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    # Extract text
    cv_service = CVAnalysisService()
    try:
        cv_text = cv_service.extract_cv_text(file_content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Analyze CV
    try:
        analysis = await cv_service.analyze_cv(cv_text, user_description)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Generate AI description
    try:
        ai_description = await cv_service.generate_ai_description(analysis, user_description)
    except ValueError:
        ai_description = None
    
    # Create or update profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    
    # Update profile with analysis
    profile.cv_file_path = file_path
    profile.cv_raw_text = cv_text
    profile.user_description = user_description
    profile.ai_description = ai_description
    profile.experiences = analysis.get("experiences", [])
    profile.skills = analysis.get("skills", [])
    profile.languages = analysis.get("languages", [])
    profile.education = analysis.get("education", [])
    profile.latest_job_title = analysis.get("latest_job_title")
    profile.years_of_experience = analysis.get("years_of_experience")
    profile.preferred_location = analysis.get("preferred_location")
    profile.cv_analyzed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    
    # Initialize default scoring criteria if not exists
    existing_criteria = db.query(ScoringCriteria).filter(
        ScoringCriteria.user_id == user.id
    ).first()
    
    if not existing_criteria:
        for criteria_config in DEFAULT_CRITERIA:
            criteria = ScoringCriteria(
                user_id=user.id,
                **criteria_config
            )
            db.add(criteria)
        db.commit()
    
    return CVUploadResponse(
        message="CV analysé avec succès. Veuillez valider les informations extraites.",
        profile=profile,
        analysis_complete=True
    )


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Update user profile.
    
    Step 4.2 from PRD: Allow user to correct extracted data.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Upload CV first.")
    
    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.put("/description", response_model=ProfileResponse)
async def update_ai_description(
    ai_description: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Update AI-generated description."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile.ai_description = ai_description
    db.commit()
    db.refresh(profile)
    
    return profile


@router.post("/regenerate-description", response_model=ProfileResponse)
async def regenerate_ai_description(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Regenerate AI description from current profile data."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    cv_service = CVAnalysisService()
    
    cv_data = {
        "experiences": profile.experiences or [],
        "skills": profile.skills or [],
        "languages": profile.languages or [],
        "education": profile.education or [],
        "latest_job_title": profile.latest_job_title,
        "years_of_experience": profile.years_of_experience
    }
    
    try:
        ai_description = await cv_service.generate_ai_description(
            cv_data, 
            profile.user_description
        )
        profile.ai_description = ai_description
        db.commit()
        db.refresh(profile)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return profile


@router.post("/confirm")
async def confirm_profile(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Confirm profile after validation.
    
    Step 4.2 from PRD: User clicks "Confirmer mon profil".
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Profile is confirmed - could add a 'confirmed' flag if needed
    # For now, just return success
    
    return {
        "message": "Profil confirmé avec succès. Vous pouvez maintenant configurer vos critères de recherche.",
        "next_step": "/criteria"
    }
