from pydantic import BaseModel
from typing import List, Optional
from .job import JobResponse


class SearchRequest(BaseModel):
    keywords: str
    location: Optional[str] = None
    platforms: List[str] = ["linkedin", "indeed"]
    remote_only: bool = False
    experience_level: Optional[str] = None
    save_results: bool = True


class SearchResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    platforms_searched: List[str]
    message: str
