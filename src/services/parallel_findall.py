"""
Service for interacting with Parallel FindAll API for comprehensive job searches.
"""
import os
import time
from typing import Dict, Any, List, Optional, Generator
from parallel import Parallel
from sqlalchemy.orm import Session

from ..models import Job, Company


class ParallelFindAllService:
    """Service for Parallel FindAll API integration."""
    
    def __init__(self, db: Session):
        self.db = db
        api_key = os.getenv("PARALLEL_API_KEY")
        if not api_key:
            raise ValueError("PARALLEL_API_KEY environment variable not set")
        
        self.client = Parallel(api_key=api_key)
        self.beta_version = os.getenv("FINDALL_BETA", "findall-2025-09-15")
        self.default_generator = os.getenv("FINDALL_DEFAULT_GENERATOR", "core")
        self.default_match_limit = int(os.getenv("FINDALL_DEFAULT_MATCH_LIMIT", "50"))
    
    def create_run(
        self,
        keywords: str,
        location: str,
        match_limit: Optional[int] = None
    ) -> str:
        """
        Create a FindAll run for job search.
        
        Args:
            keywords: Job title/role keywords (e.g., "Product Manager")
            location: City name (e.g., "Paris", "Toulouse")
            match_limit: Maximum number of matches to find (default: 50)
        
        Returns:
            findall_id: The ID of the created run
        """
        if match_limit is None:
            match_limit = self.default_match_limit
        
        # Build match conditions
        match_conditions = [
            {
                "name": "role_check",
                "description": f"Job must be for {keywords} or related role (Product Owner, PM, etc.)."
            },
            {
                "name": "location_check",
                "description": f"Job must be located in {location}, France or nearby suburbs."
            },
            {
                "name": "job_board_check",
                "description": "Job must be listed on Glassdoor, Welcome to the Jungle (welcometothejungle.com), Indeed, or LinkedIn websites."
            }
        ]
        
        # Create FindAll run
        findall_run = self.client.beta.findall.create(
            objective=f"Find all jobs for {keywords} in {location}, France on Glassdoor, Welcome to the Jungle, Indeed, and LinkedIn websites",
            entity_type="jobs",
            match_conditions=match_conditions,
            generator=self.default_generator,
            match_limit=match_limit,
            betas=[self.beta_version]
        )
        
        return findall_run.findall_id
    
    def poll_status(
        self,
        findall_id: str,
        poll_interval: int = 10,
        max_iterations: int = 120
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Poll FindAll run status and yield progress updates.
        
        Args:
            findall_id: The FindAll run ID
            poll_interval: Seconds between polls (default: 10)
            max_iterations: Maximum polling iterations (default: 120 = 20 minutes)
        
        Yields:
            Progress dict with status, generated_count, matched_count, iteration
        """
        terminal_statuses = ["completed", "failed", "cancelled"]
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                findall_run = self.client.beta.findall.retrieve(
                    findall_id=findall_id,
                    betas=[self.beta_version]
                )
                
                status = findall_run.status.status
                metrics = findall_run.status.metrics
                
                # Yield progress
                yield {
                    "status": status,
                    "generated_count": metrics.generated_candidates_count if hasattr(metrics, 'generated_candidates_count') else 0,
                    "matched_count": metrics.matched_candidates_count if hasattr(metrics, 'matched_candidates_count') else 0,
                    "iteration": iteration,
                    "is_complete": status in terminal_statuses
                }
                
                # Stop if terminal status reached
                if status in terminal_statuses:
                    break
                
                # Wait before next poll
                time.sleep(poll_interval)
                
            except Exception as e:
                yield {
                    "status": "error",
                    "error": str(e),
                    "iteration": iteration,
                    "is_complete": True
                }
                break
        
        # Check if timed out
        if iteration >= max_iterations:
            yield {
                "status": "timeout",
                "error": "Maximum polling time exceeded (20 minutes)",
                "iteration": iteration,
                "is_complete": True
            }
    
    def get_results(self, findall_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve final results from completed FindAll run.
        
        Args:
            findall_id: The FindAll run ID
        
        Returns:
            List of matched candidate dicts
        """
        result = self.client.beta.findall.result(
            findall_id=findall_id,
            betas=[self.beta_version]
        )
        
        # Extract matched candidates
        matched_candidates = [
            c for c in result.candidates 
            if c.match_status == "matched"
        ]
        
        return [self._candidate_to_dict(c) for c in matched_candidates]
    
    def _candidate_to_dict(self, candidate) -> Dict[str, Any]:
        """Convert FindAll candidate to dict."""
        output = candidate.output
        
        # Extract location from match condition output
        location_value = output.get("location_check", {}).get("value", "N/A")
        
        # Extract role type
        role_value = output.get("role_check", {}).get("value", "N/A")
        
        return {
            "candidate_id": candidate.candidate_id,
            "name": candidate.name,
            "url": candidate.url,
            "description": candidate.description,
            "match_status": candidate.match_status,
            "location": location_value,
            "role_type": role_value,
            "output": output
        }
    
    def convert_to_job_format(self, candidates: List[Dict[str, Any]]) -> List[Job]:
        """
        Convert FindAll candidates to Job model instances.
        
        Args:
            candidates: List of candidate dicts from get_results()
        
        Returns:
            List of Job instances (not yet committed to DB)
        """
        jobs = []
        
        for candidate in candidates:
            # Check if job already exists by URL
            existing = self.db.query(Job).filter(
                Job.source_url == candidate["url"]
            ).first()
            
            if existing:
                continue
            
            # Extract company name from job title
            company_name = self._extract_company_name(candidate["name"])
            company_id = None
            
            if company_name:
                company = self._get_or_create_company(company_name)
                company_id = company.id
            
            # Create Job instance
            job = Job(
                title=candidate["name"],
                description=candidate.get("description", ""),
                location=candidate.get("location", ""),
                source_url=candidate["url"],
                source_platform="findall",
                external_id=candidate["candidate_id"],
                company_id=company_id,
                # FindAll provides high-quality matches
                salary_min=None,  # Could add via enrichments
                salary_max=None,
                job_type=None,
                experience_level=None,
                remote_type=None
            )
            
            jobs.append(job)
        
        return jobs
    
    def _extract_company_name(self, job_title: str) -> Optional[str]:
        """Extract company name from job title."""
        # Common patterns: "Title – Company" or "Title at Company"
        if "–" in job_title:
            parts = job_title.split("–")
            if len(parts) >= 2:
                company = parts[1].strip().split(",")[0].strip()
                return company
        elif " at " in job_title.lower():
            parts = job_title.lower().split(" at ")
            if len(parts) >= 2:
                company = parts[1].strip().split(",")[0].strip()
                return company
        
        return None
    
    def _get_or_create_company(self, company_name: str) -> Company:
        """Get existing company or create new one."""
        company = self.db.query(Company).filter(
            Company.name == company_name
        ).first()
        
        if not company:
            company = Company(name=company_name)
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
        
        return company
    
    def save_jobs(self, jobs: List[Job]) -> List[Job]:
        """
        Save jobs to database.
        
        Args:
            jobs: List of Job instances
        
        Returns:
            List of saved Job instances with IDs
        """
        for job in jobs:
            self.db.add(job)
        
        self.db.commit()
        
        # Refresh to get IDs
        for job in jobs:
            self.db.refresh(job)
        
        return jobs
