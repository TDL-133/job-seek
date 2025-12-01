"""
FindAll search router with SSE streaming support.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import asyncio
import logging
from typing import Optional
from jose import JWTError, jwt
import os

from ..models import get_db, User, UserScoringPreferences, UserProfile, DEFAULT_SCORING_PREFERENCES
from ..services.parallel_findall import ParallelFindAllService
from ..services.scoring_v2 import scoring_service_v2

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


router = APIRouter()

# Store active findall runs in memory (for resume functionality)
active_runs: dict = {}

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """Validate JWT token and return user."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except JWTError:
        return None


def get_user_scoring_prefs(user: User, db: Session) -> dict:
    """Get user scoring preferences for V2 scoring."""
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
    
    # Get CV skills from profile
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user.id
    ).first()
    
    cv_skills = []
    if profile and profile.skills:
        cv_skills = profile.skills if isinstance(profile.skills, list) else []
    
    scoring_prefs = prefs.to_dict()
    scoring_prefs["cv_skills"] = cv_skills
    
    return scoring_prefs


@router.get("/status/{findall_id}")
async def get_findall_status(
    findall_id: str,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
    db: Session = Depends(get_db)
):
    """
    Get status of an existing FindAll run.
    """
    user = None
    if token:
        user = get_user_from_token(token, db)
    
    findall_service = ParallelFindAllService(db)
    
    try:
        # Use the underlying client to get status
        run = findall_service.client.beta.findall.retrieve(
            findall_id=findall_id,
            betas=[findall_service.beta_version]
        )
        
        return {
            "findall_id": findall_id,
            "status": run.status.status,
            "generated_count": run.status.metrics.generated_candidates_count if hasattr(run.status.metrics, 'generated_candidates_count') else 0,
            "matched_count": run.status.metrics.matched_candidates_count if hasattr(run.status.metrics, 'matched_candidates_count') else 0,
            "is_complete": run.status.status in ["completed", "failed", "cancelled"]
        }
    except Exception as e:
        logger.error(f"Error getting FindAll status: {e}")
        return {"error": str(e)}


@router.get("/stream")
async def search_findall_stream(
    keywords: str = Query(..., description="Search keywords (job title)"),
    location: str = Query(..., description="City location"),
    token: Optional[str] = Query(None, description="JWT token for authentication"),
    match_limit: Optional[int] = Query(None, description="Maximum matches (default: 50)"),
    resume_id: Optional[str] = Query(None, description="Resume existing FindAll run by ID"),
    db: Session = Depends(get_db)
):
    """
    Deep search using FindAll API with Server-Sent Events streaming.
    
    Returns events:
    - findall_created: {findall_id, status}
    - findall_progress: {status, generated_count, matched_count, iteration, elapsed}
    - findall_complete: {findall_id, total_matched, execution_time}
    - error: {message}
    
    Execution time: ~10-20 minutes for 20-50 matches
    """
    
    # Get user for scoring (optional - allows anonymous search but without scoring)
    user = None
    scoring_prefs = None
    if token:
        user = get_user_from_token(token, db)
        if user:
            scoring_prefs = get_user_scoring_prefs(user, db)
    
    async def event_generator():
        start_time = asyncio.get_event_loop().time()
        
        try:
            findall_service = ParallelFindAllService(db)
            logger.info("ParallelFindAllService initialized successfully")
            
            # Step 1: Create or resume FindAll run
            if resume_id:
                findall_id = resume_id
                logger.info(f"Resuming existing FindAll run: {findall_id}")
                yield f"data: {json.dumps({'event': 'findall_resumed', 'findall_id': findall_id, 'status': 'resuming'})}\n\n"
            else:
                logger.info(f"Starting FindAll search: keywords='{keywords}', location='{location}'")
                logger.info("Creating FindAll run...")
                findall_id = findall_service.create_run(
                    keywords=keywords,
                    location=location,
                    match_limit=match_limit
                )
                logger.info(f"FindAll run created: {findall_id}")
                # Store for potential resume
                active_runs[f"{keywords}_{location}"] = findall_id
                yield f"data: {json.dumps({'event': 'findall_created', 'findall_id': findall_id, 'status': 'queued'})}\n\n"
            
            # Step 2: Poll for progress with keepalive
            progress = None
            last_keepalive = asyncio.get_event_loop().time()
            
            async for progress in findall_service.poll_status(findall_id):
                current_time = asyncio.get_event_loop().time()
                elapsed = int(current_time - start_time)
                
                # Add elapsed time
                progress['elapsed'] = elapsed
                
                # Emit progress event
                yield f"data: {json.dumps({'event': 'findall_progress', **progress})}\n\n"
                
                # Send keepalive comment every 5 seconds to prevent timeout
                if current_time - last_keepalive > 5:
                    yield f": keepalive {elapsed}s\n\n"
                    last_keepalive = current_time
                
                # Check if complete
                if progress.get('is_complete'):
                    break
            
            # Step 3: Get final results
            if progress and progress.get('status') == 'completed':
                candidates = findall_service.get_results(findall_id)
                
                # Convert to Job models
                jobs = findall_service.convert_to_job_format(candidates)
                
                # Save to database
                saved_jobs = findall_service.save_jobs(jobs)
                
                # Score jobs with V2 scoring if user is authenticated
                scored_jobs = []
                for job in saved_jobs:
                    job_dict = {
                        "id": job.id,
                        "title": job.title,
                        "company": job.company.name if job.company else None,
                        "location": job.location,
                        "description": job.description or "",
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
                    
                    # Calculate V2 score if user preferences available
                    if scoring_prefs:
                        score_result = scoring_service_v2.calculate_total_score(job_dict, scoring_prefs)
                        scored_jobs.append({
                            "job": job_dict,
                            "score": score_result["score"],
                            "breakdown": score_result["breakdown"]
                        })
                    else:
                        # No scoring - just return job data
                        scored_jobs.append({
                            "job": job_dict,
                            "score": 0,
                            "breakdown": {}
                        })
                
                # Sort by score (highest first)
                scored_jobs.sort(key=lambda x: x["score"], reverse=True)
                
                # Emit complete event
                execution_time = int(asyncio.get_event_loop().time() - start_time)
                yield f"data: {json.dumps({'event': 'findall_complete', 'findall_id': findall_id, 'total_matched': len(scored_jobs), 'execution_time': execution_time, 'jobs': scored_jobs})}\n\n"
            else:
                # Run did not complete successfully
                error_msg = progress.get('error', 'FindAll run did not complete') if progress else 'No progress received'
                yield f"data: {json.dumps({'event': 'error', 'message': error_msg})}\n\n"
        
        except Exception as e:
            # Emit error event
            logger.error(f"FindAll error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
