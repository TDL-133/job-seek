"""
Unipile API client service for LinkedIn integration.

This service handles all interactions with the Unipile API for LinkedIn
job search, profile retrieval, and people search.
"""
import os
import httpx
from typing import Dict, List, Optional, Any
import asyncio
import random


class UnipileService:
    """Service for interacting with Unipile API."""
    
    def __init__(self):
        self.dsn = os.getenv("UNIPILE_DSN", "https://api21.unipile.com:15160")
        self.api_key = os.getenv("UNIPILE_API_KEY", "")
        self.linkedin_account_id = os.getenv("UNIPILE_LINKEDIN_ACCOUNT_ID", "")
        
        self.headers = {
            "X-API-KEY": self.api_key,
            "accept": "application/json",
            "content-type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Check if Unipile is properly configured."""
        return bool(self.api_key and self.linkedin_account_id)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: float = 30.0
    ) -> Optional[Dict]:
        """Make an HTTP request to the Unipile API."""
        url = f"{self.dsn}{endpoint}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, params=params, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Unipile API error: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                print(f"Unipile request error: {e}")
                return None
    
    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn via Unipile API.
        
        Args:
            keywords: Search keywords (job title, skills, etc.)
            location: Location filter
            remote_only: Filter for remote jobs only
            experience_level: Filter by experience level
            limit: Maximum number of results (max 100 per request)
            
        Returns:
            List of job dictionaries
        """
        if not self.is_configured():
            print("Unipile not configured, skipping LinkedIn job search")
            return []
        
        # Build search parameters
        search_params = {
            "api": "classic",
            "category": "jobs",
            "keywords": keywords,
        }
        
        # Add location if provided (need to get location IDs for proper filtering)
        if location:
            search_params["keywords"] = f"{keywords} {location}"
        
        # Remote filter - f_WT parameter in LinkedIn
        if remote_only:
            search_params["workplace_type"] = ["remote"]
        
        # Experience level mapping
        exp_mapping = {
            "entry": "1",
            "associate": "2", 
            "mid": "3",
            "senior": "4",
            "director": "5",
            "executive": "6"
        }
        if experience_level and experience_level.lower() in exp_mapping:
            search_params["experience_level"] = [exp_mapping[experience_level.lower()]]
        
        # Add small random delay to emulate human behavior
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        result = await self._make_request(
            "POST",
            "/api/v1/linkedin/search",
            params={"account_id": self.linkedin_account_id},
            json_data=search_params
        )
        
        if not result or "items" not in result:
            return []
        
        jobs = []
        for item in result.get("items", [])[:limit]:
            job = self._parse_job(item)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job(self, item: Dict) -> Optional[Dict]:
        """Parse a job item from Unipile search results."""
        if item.get("type") != "JOB":
            return None
        
        # Map workplace_type to remote_type
        workplace = item.get("workplace_type", "").lower()
        if workplace == "remote":
            remote_type = "remote"
        elif workplace == "hybrid":
            remote_type = "hybrid"
        else:
            remote_type = "onsite"
        
        # Extract company info
        company = item.get("company", {})
        company_name = company.get("name") if isinstance(company, dict) else item.get("company_name")
        
        return {
            "title": item.get("title"),
            "company_name": company_name,
            "location": item.get("location"),
            "remote_type": remote_type,
            "source_url": item.get("job_url") or item.get("url"),
            "source_platform": "linkedin",
            "external_id": item.get("id"),
            "description": item.get("description"),
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "EUR",
            "job_type": item.get("employment_type"),
            "experience_level": item.get("seniority_level"),
            "skills": [],
            "benefits": [],
            "easy_apply": item.get("easy_apply", False),
            "posted_at": item.get("posted_at"),
        }
    
    async def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Fetch detailed job information.
        
        Note: This may require additional API calls and should be used sparingly
        due to rate limits.
        """
        if not self.is_configured():
            return None
        
        # Add delay for rate limiting
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Unipile doesn't have a direct job details endpoint
        # Job details are typically included in search results
        # This is a placeholder for future enhancement
        return None
    
    async def search_people(
        self,
        keywords: str,
        location: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict]:
        """
        Search for people on LinkedIn.
        
        Args:
            keywords: Search keywords
            location: Location filter
            limit: Maximum results
            
        Returns:
            List of people profiles
        """
        if not self.is_configured():
            return []
        
        search_params = {
            "api": "classic",
            "category": "people",
            "keywords": keywords,
        }
        
        if location:
            search_params["keywords"] = f"{keywords} {location}"
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        result = await self._make_request(
            "POST",
            "/api/v1/linkedin/search",
            params={"account_id": self.linkedin_account_id},
            json_data=search_params
        )
        
        if not result or "items" not in result:
            return []
        
        people = []
        for item in result.get("items", [])[:limit]:
            if item.get("type") == "PEOPLE":
                people.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "first_name": item.get("first_name"),
                    "last_name": item.get("last_name"),
                    "headline": item.get("headline"),
                    "location": item.get("location"),
                    "profile_url": item.get("profile_url"),
                    "public_identifier": item.get("public_identifier"),
                    "network_distance": item.get("network_distance"),
                })
        
        return people
    
    async def get_profile(self, identifier: str) -> Optional[Dict]:
        """
        Get a LinkedIn profile by public identifier or provider ID.
        
        Args:
            identifier: Public profile ID (e.g., "julien-crepieux") or provider ID
            
        Returns:
            Profile data or None if not found
        """
        if not self.is_configured():
            return None
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        result = await self._make_request(
            "GET",
            f"/api/v1/users/{identifier}",
            params={"account_id": self.linkedin_account_id}
        )
        
        return result
    
    async def get_relations(self, limit: int = 100) -> List[Dict]:
        """
        Get all LinkedIn connections/relations.
        
        Returns:
            List of connection profiles
        """
        if not self.is_configured():
            return []
        
        result = await self._make_request(
            "GET",
            "/api/v1/users/relations",
            params={
                "account_id": self.linkedin_account_id,
                "limit": limit
            }
        )
        
        if not result or "items" not in result:
            return []
        
        return result.get("items", [])
    
    async def check_account_status(self) -> Optional[Dict]:
        """
        Check the status of the connected LinkedIn account.
        
        Returns:
            Account info or None if not available
        """
        if not self.api_key:
            return None
        
        result = await self._make_request("GET", "/api/v1/accounts")
        
        if not result or "items" not in result:
            return None
        
        # Find the LinkedIn account
        for account in result.get("items", []):
            if account.get("id") == self.linkedin_account_id:
                return {
                    "id": account.get("id"),
                    "name": account.get("name"),
                    "type": account.get("type"),
                    "status": account.get("sources", [{}])[0].get("status", "UNKNOWN"),
                    "public_identifier": account.get("connection_params", {}).get("im", {}).get("publicIdentifier")
                }
        
        return None


# Singleton instance for convenience
_unipile_service: Optional[UnipileService] = None


def get_unipile_service() -> UnipileService:
    """Get or create the Unipile service instance."""
    global _unipile_service
    if _unipile_service is None:
        _unipile_service = UnipileService()
    return _unipile_service
