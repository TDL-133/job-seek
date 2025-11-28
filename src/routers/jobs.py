from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..models import get_db, Job, User, UserScoringPreferences, UserProfile, DEFAULT_SCORING_PREFERENCES
from ..schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse
from ..services.auth import get_current_user_required
from ..services.scoring_v2 import scoring_service_v2

router = APIRouter()


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    title: Optional[str] = None,
    location: Optional[str] = None,
    remote_type: Optional[str] = None,
    source_platform: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """List all jobs with optional filters."""
    query = db.query(Job).filter(Job.is_active == is_active)
    
    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if remote_type:
        query = query.filter(Job.remote_type == remote_type)
    if source_platform:
        query = query.filter(Job.source_platform == source_platform)
    
    total = query.count()
    jobs = query.offset(skip).limit(limit).all()
    
    return JobListResponse(jobs=jobs, total=total, skip=skip, limit=limit)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=JobResponse)
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new job listing."""
    # Check if job with same source_url already exists
    existing = db.query(Job).filter(Job.source_url == job.source_url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Job with this URL already exists")
    
    db_job = Job(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job: JobUpdate, db: Session = Depends(get_db)):
    """Update a job listing."""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job listing."""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(db_job)
    db.commit()
    return {"message": "Job deleted successfully"}


# ============================================================================
# V2 Scoring Endpoints
# ============================================================================

class ScoredJobResponse(BaseModel):
    """Job response with V2 score breakdown."""
    job: Dict[str, Any]
    score: float
    breakdown: Dict[str, Any]


class ScoredJobsListResponse(BaseModel):
    """List of scored jobs."""
    jobs: List[ScoredJobResponse]
    total: int
    skip: int
    limit: int


@router.get("/scored/v2", response_model=ScoredJobsListResponse)
async def list_scored_jobs_v2(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    title: Optional[str] = None,
    location: Optional[str] = None,
    remote_type: Optional[str] = None,
    source_platform: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    is_active: bool = True,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    List jobs with V2 scoring (fixed-point system).
    
    Jobs are sorted by score (highest first).
    """
    # Get user preferences
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
    
    # Get user profile for CV skills
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user.id
    ).first()
    
    cv_skills = []
    if profile and profile.skills:
        cv_skills = profile.skills if isinstance(profile.skills, list) else []
    
    # Build preferences dict for scoring
    scoring_prefs = prefs.to_dict()
    scoring_prefs["cv_skills"] = cv_skills
    
    # Query jobs
    query = db.query(Job).filter(Job.is_active == is_active)
    
    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if remote_type:
        query = query.filter(Job.remote_type == remote_type)
    if source_platform:
        query = query.filter(Job.source_platform == source_platform)
    
    jobs = query.all()
    
    # Score all jobs
    scored_jobs = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company": job.company.name if job.company else None,
            "location": job.location,
            "description": job.description,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "remote_type": job.remote_type,
            "job_type": job.job_type,
            "experience_level": job.experience_level,
            "skills": job.skills if job.skills else [],
            "source": job.source_platform,
            "source_url": job.source_url,
            "posted_at": job.posted_date.isoformat() if job.posted_date else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
        
        score_result = scoring_service_v2.calculate_total_score(job_dict, scoring_prefs)
        
        # Filter by min_score if specified
        if min_score is not None and score_result["score"] < min_score:
            continue
        
        scored_jobs.append(ScoredJobResponse(
            job=job_dict,
            score=score_result["score"],
            breakdown=score_result["breakdown"]
        ))
    
    # Sort by score (highest first)
    scored_jobs.sort(key=lambda x: x.score, reverse=True)
    
    # Apply pagination
    total = len(scored_jobs)
    paginated_jobs = scored_jobs[skip:skip + limit]
    
    return ScoredJobsListResponse(
        jobs=paginated_jobs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{job_id}/score/v2")
async def get_job_score_v2(
    job_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Get V2 score breakdown for a specific job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get user preferences
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
    
    # Get user profile for CV skills
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user.id
    ).first()
    
    cv_skills = []
    if profile and profile.skills:
        cv_skills = profile.skills if isinstance(profile.skills, list) else []
    
    # Build preferences dict for scoring
    scoring_prefs = prefs.to_dict()
    scoring_prefs["cv_skills"] = cv_skills
    
    job_dict = {
        "id": job.id,
        "title": job.title,
        "company": job.company.name if job.company else None,
        "location": job.location,
        "description": job.description,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "remote_type": job.remote_type,
        "job_type": job.job_type,
        "experience_level": job.experience_level,
            "skills": job.skills if job.skills else [],
            "source": job.source_platform,
            "source_url": job.source_url,
            "posted_at": job.posted_date.isoformat() if job.posted_date else None,
        }
    
    score_result = scoring_service_v2.calculate_total_score(job_dict, scoring_prefs)
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "score": score_result["score"],
        "breakdown": score_result["breakdown"]
    }
