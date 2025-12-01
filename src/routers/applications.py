from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from ..models import get_db, Application, ApplicationStatus, Job, User
from ..schemas.application import (
    ApplicationCreate, 
    ApplicationUpdate, 
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationWithJobResponse,
    ApplicationWithJobListResponse
)
from ..services.auth import get_current_user_required

router = APIRouter()


@router.get("/", response_model=ApplicationWithJobListResponse)
async def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ApplicationStatus] = None,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """List user's applications with optional status filter."""
    query = db.query(Application).options(joinedload(Application.job)).filter(
        Application.user_id == current_user.id
    )
    
    if status:
        query = query.filter(Application.status == status)
    
    total = query.count()
    applications = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
    
    return ApplicationWithJobListResponse(
        applications=applications, 
        total=total, 
        skip=skip, 
        limit=limit
    )


@router.get("/stats")
async def get_application_stats(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get user's application statistics by status."""
    stats = {}
    for status in ApplicationStatus:
        count = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.status == status
        ).count()
        stats[status.value] = count
    return stats


@router.get("/{application_id}", response_model=ApplicationWithJobResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get a specific application by ID."""
    application = db.query(Application).options(joinedload(Application.job)).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application: ApplicationCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Create a new application (save a job)."""
    # Check if application already exists for this user and job
    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == application.job_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already saved this job")
    
    db_application = Application(
        **application.model_dump(),
        user_id=current_user.id
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int, 
    application: ApplicationUpdate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Update an application."""
    db_application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = application.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_application, field, value)
    
    db.commit()
    db.refresh(db_application)
    return db_application


@router.post("/{application_id}/apply", response_model=ApplicationResponse)
async def mark_as_applied(
    application_id: int,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Mark an application as applied."""
    db_application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db_application.status = ApplicationStatus.APPLIED
    db_application.applied_at = datetime.utcnow()
    db.commit()
    db.refresh(db_application)
    return db_application


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Delete an application."""
    db_application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(db_application)
    db.commit()
    return {"message": "Application deleted successfully"}
