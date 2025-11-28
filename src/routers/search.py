from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import asyncio

from ..models import get_db
from ..schemas.search import SearchRequest, SearchResponse
from ..services.job_search import JobSearchService

router = APIRouter()


@router.post("/jobs", response_model=SearchResponse)
async def search_jobs(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Search for jobs across multiple platforms.
    
    Supported platforms: linkedin, indeed, glassdoor, welcometothejungle
    """
    search_service = JobSearchService(db)
    
    try:
        results = await search_service.search(
            keywords=request.keywords,
            location=request.location,
            platforms=request.platforms,
            remote_only=request.remote_only,
            experience_level=request.experience_level,
            save_results=request.save_results
        )
        
        return SearchResponse(
            jobs=results["jobs"],
            total=results["total"],
            platforms_searched=results["platforms_searched"],
            message="Search completed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/{platform}")
async def scrape_platform(
    platform: str,
    keywords: str,
    location: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Scrape jobs from a specific platform."""
    supported_platforms = ["linkedin", "indeed", "glassdoor", "welcometothejungle"]
    
    if platform.lower() not in supported_platforms:
        raise HTTPException(
            status_code=400, 
            detail=f"Platform not supported. Choose from: {supported_platforms}"
        )
    
    search_service = JobSearchService(db)
    
    try:
        results = await search_service.scrape_platform(
            platform=platform.lower(),
            keywords=keywords,
            location=location,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/stream")
async def search_jobs_stream(
    keywords: str = Query(..., description="Search keywords"),
    location: Optional[str] = Query(None, description="Location filter"),
    platforms: Optional[str] = Query(None, description="Comma-separated platforms"),
    save_results: bool = Query(True, description="Save to database"),
    db: Session = Depends(get_db)
):
    """
    Stream job search with Server-Sent Events.
    
    Returns events:
    - scanning_start: {platform: str}
    - scanning_complete: {platform: str, count: int, jobs: list}
    - search_complete: {total: int, platforms_searched: list}
    - error: {platform: str, message: str}
    """
    platform_list = platforms.split(",") if platforms else ["linkedin", "indeed", "glassdoor", "welcometothejungle"]
    
    async def event_generator():
        search_service = JobSearchService(db)
        all_jobs = []
        platforms_searched = []
        
        for platform in platform_list:
            platform = platform.strip().lower()
            if platform not in search_service.scrapers:
                continue
            
            # Send scanning_start event
            yield f"data: {json.dumps({'event': 'scanning_start', 'platform': platform})}\n\n"
            
            try:
                jobs = await search_service.scrape_platform(
                    platform=platform,
                    keywords=keywords,
                    location=location,
                    limit=25
                )
                
                job_list = jobs.get("jobs", [])
                
                # Save jobs to database if requested
                if save_results and job_list:
                    saved_jobs = search_service._save_jobs(job_list)
                    # Convert to dicts for JSON serialization
                    job_list = [
                        {
                            "id": j.id,
                            "title": j.title,
                            "company": j.company.name if j.company else None,
                            "location": j.location,
                            "source": j.source_platform,
                            "source_url": j.source_url,
                        }
                        for j in saved_jobs
                    ]
                
                all_jobs.extend(job_list)
                platforms_searched.append(platform)
                
                # Send scanning_complete event
                yield f"data: {json.dumps({'event': 'scanning_complete', 'platform': platform, 'count': len(job_list), 'jobs': job_list})}\n\n"
                
            except Exception as e:
                # Send error event
                yield f"data: {json.dumps({'event': 'error', 'platform': platform, 'message': str(e)})}\n\n"
            
            # Small delay between platforms
            await asyncio.sleep(0.5)
        
        # Send final search_complete event
        yield f"data: {json.dumps({'event': 'search_complete', 'total': len(all_jobs), 'platforms_searched': platforms_searched})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
