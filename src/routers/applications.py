from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models import get_db, Application, ApplicationStatus
from ..schemas.application import (
    ApplicationCreate, 
    ApplicationUpdate, 
    ApplicationResponse,
    ApplicationListResponse
)

router = APIRouter()


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ApplicationStatus] = None,
    db: Session = Depends(get_db)
):
    """List all applications with optional status filter."""
    query = db.query(Application)
    
    if status:
        query = query.filter(Application.status == status)
    
    total = query.count()
    applications = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
    
    return ApplicationListResponse(
        applications=applications, 
        total=total, 
        skip=skip, 
        limit=limit
    )


@router.get("/stats")
async def get_application_stats(db: Session = Depends(get_db)):
    """Get application statistics by status."""
    stats = {}
    for status in ApplicationStatus:
        count = db.query(Application).filter(Application.status == status).count()
        stats[status.value] = count
    return stats


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: int, db: Session = Depends(get_db)):
    """Get a specific application by ID."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application: ApplicationCreate, 
    db: Session = Depends(get_db)
):
    """Create a new application."""
    db_application = Application(**application.model_dump())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int, 
    application: ApplicationUpdate, 
    db: Session = Depends(get_db)
):
    """Update an application."""
    db_application = db.query(Application).filter(Application.id == application_id).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = application.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_application, field, value)
    
    db.commit()
    db.refresh(db_application)
    return db_application


@router.post("/{application_id}/apply", response_model=ApplicationResponse)
async def mark_as_applied(application_id: int, db: Session = Depends(get_db)):
    """Mark an application as applied."""
    db_application = db.query(Application).filter(Application.id == application_id).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db_application.status = ApplicationStatus.APPLIED
    db_application.applied_at = datetime.utcnow()
    db.commit()
    db.refresh(db_application)
    return db_application


@router.delete("/{application_id}")
async def delete_application(application_id: int, db: Session = Depends(get_db)):
    """Delete an application."""
    db_application = db.query(Application).filter(Application.id == application_id).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(db_application)
    db.commit()
    return {"message": "Application deleted successfully"}
