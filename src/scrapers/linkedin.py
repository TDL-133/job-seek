from typing import List, Dict, Optional
from urllib.parse import quote_plus
from .base import BaseScraper
from bs4 import BeautifulSoup

# Import Unipile service for LinkedIn API integration
from ..services.unipile import get_unipile_service


class LinkedInScraper(BaseScraper):
    """
    LinkedIn job scraper using Unipile API.
    
    This scraper uses the Unipile API for authenticated LinkedIn job search,
    which provides more reliable and comprehensive results than web scraping.
    Falls back to web scraping if Unipile is not configured.
    """
    
    def __init__(self):
        super().__init__()
        self.platform_name = "linkedin"
        self.base_url = "https://www.linkedin.com/jobs/search"
        self._unipile = None
    
    @property
    def unipile(self):
        """Lazy-load Unipile service."""
        if self._unipile is None:
            self._unipile = get_unipile_service()
        return self._unipile
    
    async def search(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search LinkedIn for jobs using Unipile API.
        
        Falls back to web scraping if Unipile is not configured or fails.
        """
        # Try Unipile API first
        if self.unipile.is_configured():
            try:
                jobs = await self.unipile.search_jobs(
                    keywords=keywords,
                    location=location,
                    remote_only=remote_only,
                    experience_level=experience_level,
                    limit=limit
                )
                if jobs:
                    print(f"LinkedIn: Found {len(jobs)} jobs via Unipile API")
                    return jobs
            except Exception as e:
                print(f"Unipile API error, falling back to web scraping: {e}")
        
        # Fallback to web scraping
        return await self._search_web_scraping(
            keywords, location, remote_only, experience_level, limit
        )
    
    async def _search_web_scraping(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Fallback web scraping method for LinkedIn jobs.
        
        Note: This method is less reliable due to LinkedIn's anti-scraping measures.
        """
        jobs = []
        
        # Build search URL
        params = [f"keywords={quote_plus(keywords)}"]
        
        if location:
            params.append(f"location={quote_plus(location)}")
        
        if remote_only:
            params.append("f_WT=2")  # Remote filter
        
        # Experience level mapping
        exp_mapping = {
            "entry": "1",
            "mid": "2",
            "senior": "3",
            "director": "4",
            "executive": "5"
        }
        if experience_level and experience_level.lower() in exp_mapping:
            params.append(f"f_E={exp_mapping[experience_level.lower()]}")
        
        url = f"{self.base_url}?{'&'.join(params)}"
        
        html = await self.fetch_page(url)
        if not html:
            return jobs
        
        soup = BeautifulSoup(html, "lxml")
        
        # Parse job cards from public LinkedIn jobs page
        job_cards = soup.find_all("div", class_="base-card")[:limit]
        
        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"Error parsing LinkedIn job card: {e}")
                continue
        
        print(f"LinkedIn: Found {len(jobs)} jobs via web scraping")
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a LinkedIn job card from web scraping."""
        title_elem = card.find("h3", class_="base-search-card__title")
        company_elem = card.find("h4", class_="base-search-card__subtitle")
        location_elem = card.find("span", class_="job-search-card__location")
        link_elem = card.find("a", class_="base-card__full-link")
        
        if not title_elem or not link_elem:
            return None
        
        title = self.clean_text(title_elem.get_text())
        company_name = self.clean_text(company_elem.get_text()) if company_elem else None
        location = self.clean_text(location_elem.get_text()) if location_elem else None
        job_url = link_elem.get("href", "")
        
        # Determine remote type
        remote_type = None
        if location:
            location_lower = location.lower()
            if "remote" in location_lower:
                remote_type = "remote"
            elif "hybrid" in location_lower:
                remote_type = "hybrid"
            else:
                remote_type = "onsite"
        
        return {
            "title": title,
            "company_name": company_name,
            "location": location,
            "remote_type": remote_type,
            "source_url": job_url,
            "source_platform": self.platform_name,
            "description": None,  # Would need to fetch job detail page
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "EUR",
            "job_type": None,
            "experience_level": None,
            "skills": [],
            "benefits": [],
        }
