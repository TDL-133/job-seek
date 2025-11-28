from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import asyncio

from ..models import Job, Company
from ..scrapers import LinkedInScraper, IndeedScraper, GlassdoorScraper, WTTJScraper


class JobSearchService:
    """Service for searching and scraping jobs from multiple platforms."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scrapers = {
            "linkedin": LinkedInScraper(),
            "indeed": IndeedScraper(),
            "glassdoor": GlassdoorScraper(),
            "welcometothejungle": WTTJScraper(),
        }
    
    async def search(
        self,
        keywords: str,
        location: Optional[str] = None,
        platforms: List[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Search for jobs across multiple platforms.
        
        Args:
            keywords: Search keywords (job title, skills, etc.)
            location: Location filter
            platforms: List of platforms to search (default: all)
            remote_only: Filter for remote jobs only
            experience_level: Filter by experience level
            save_results: Whether to save results to database
            
        Returns:
            Dict containing jobs, total count, and platforms searched
        """
        if platforms is None:
            platforms = list(self.scrapers.keys())
        
        all_jobs = []
        platforms_searched = []
        
        # Run scrapers concurrently
        tasks = []
        for platform in platforms:
            if platform in self.scrapers:
                tasks.append(
                    self._scrape_platform(
                        platform, keywords, location, remote_only, experience_level
                    )
                )
                platforms_searched.append(platform)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                print(f"Scraping error: {result}")
        
        # Save results to database if requested
        if save_results:
            saved_jobs = self._save_jobs(all_jobs)
            return {
                "jobs": saved_jobs,
                "total": len(saved_jobs),
                "platforms_searched": platforms_searched
            }
        
        return {
            "jobs": all_jobs,
            "total": len(all_jobs),
            "platforms_searched": platforms_searched
        }
    
    async def _scrape_platform(
        self,
        platform: str,
        keywords: str,
        location: Optional[str],
        remote_only: bool,
        experience_level: Optional[str]
    ) -> List[Dict]:
        """Scrape a single platform."""
        scraper = self.scrapers[platform]
        return await scraper.search(
            keywords=keywords,
            location=location,
            remote_only=remote_only,
            experience_level=experience_level
        )
    
    async def scrape_platform(
        self,
        platform: str,
        keywords: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Scrape jobs from a specific platform."""
        if platform not in self.scrapers:
            raise ValueError(f"Unknown platform: {platform}")
        
        scraper = self.scrapers[platform]
        jobs = await scraper.search(
            keywords=keywords,
            location=location,
            limit=limit
        )
        
        return {
            "platform": platform,
            "jobs": jobs,
            "total": len(jobs)
        }
    
    def _save_jobs(self, jobs: List[Dict]) -> List[Job]:
        """Save scraped jobs to database, avoiding duplicates."""
        saved_jobs = []
        
        for job_data in jobs:
            # Check if job already exists by source_url
            existing = self.db.query(Job).filter(
                Job.source_url == job_data.get("source_url")
            ).first()
            
            if existing:
                continue
            
            # Handle company
            company_id = None
            if job_data.get("company_name"):
                company = self._get_or_create_company(job_data)
                company_id = company.id
            
            # Create job
            job = Job(
                title=job_data.get("title"),
                description=job_data.get("description"),
                requirements=job_data.get("requirements"),
                location=job_data.get("location"),
                remote_type=job_data.get("remote_type"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                salary_currency=job_data.get("salary_currency", "EUR"),
                job_type=job_data.get("job_type"),
                experience_level=job_data.get("experience_level"),
                source_url=job_data.get("source_url"),
                source_platform=job_data.get("source_platform"),
                external_id=job_data.get("external_id"),
                skills=job_data.get("skills"),
                benefits=job_data.get("benefits"),
                company_id=company_id
            )
            
            self.db.add(job)
            saved_jobs.append(job)
        
        self.db.commit()
        
        # Refresh to get IDs
        for job in saved_jobs:
            self.db.refresh(job)
        
        return saved_jobs
    
    def _get_or_create_company(self, job_data: Dict) -> Company:
        """Get existing company or create new one."""
        company_name = job_data.get("company_name")
        
        company = self.db.query(Company).filter(
            Company.name == company_name
        ).first()
        
        if not company:
            company = Company(
                name=company_name,
                website=job_data.get("company_website"),
                linkedin_url=job_data.get("company_linkedin"),
                logo_url=job_data.get("company_logo"),
                industry=job_data.get("company_industry"),
            )
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
        
        return company
