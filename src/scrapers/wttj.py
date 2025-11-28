from typing import List, Dict, Optional
from urllib.parse import quote_plus
from .base import BaseScraper
from bs4 import BeautifulSoup


class WTTJScraper(BaseScraper):
    """
    Welcome to the Jungle job scraper.
    
    WTTJ is popular in France and Europe for tech jobs.
    """
    
    def __init__(self):
        super().__init__()
        self.platform_name = "welcometothejungle"
        self.base_url = "https://www.welcometothejungle.com/fr/jobs"
    
    async def search(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search Welcome to the Jungle for jobs.
        
        For better results, use MCP tools (firecrawl, playwright) configured
        in your environment for enhanced scraping capabilities.
        """
        jobs = []
        
        # Build search URL
        params = [f"query={quote_plus(keywords)}"]
        
        if location:
            params.append(f"aroundQuery={quote_plus(location)}")
        
        if remote_only:
            params.append("remote=true")
        
        # Contract type filter would go here
        # Experience level mapping for WTTJ
        
        url = f"{self.base_url}?{'&'.join(params)}"
        
        html = await self.fetch_page(url)
        if not html:
            return jobs
        
        soup = BeautifulSoup(html, "lxml")
        
        # Parse job cards
        job_cards = soup.find_all("article", {"data-testid": "search-results-list-item-wrapper"})[:limit]
        
        if not job_cards:
            # Try alternative selector
            job_cards = soup.find_all("div", class_="ais-Hits-item")[:limit]
        
        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"Error parsing WTTJ job card: {e}")
                continue
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a WTTJ job card."""
        # WTTJ uses various selectors
        title_elem = card.find("h4") or card.find("span", class_="job-title")
        company_elem = card.find("span", {"data-testid": "search-results-list-item-company-name"})
        location_elem = card.find("span", {"data-testid": "search-results-list-item-contract-location"})
        link_elem = card.find("a", href=True)
        
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.get_text())
        company_name = self.clean_text(company_elem.get_text()) if company_elem else None
        location = self.clean_text(location_elem.get_text()) if location_elem else None
        
        # Get job URL
        job_url = ""
        if link_elem:
            href = link_elem.get("href", "")
            if href.startswith("/"):
                job_url = f"https://www.welcometothejungle.com{href}"
            else:
                job_url = href
        
        # Determine remote type from WTTJ specific indicators
        remote_type = None
        if location:
            location_lower = location.lower()
            if "remote" in location_lower or "télétravail" in location_lower:
                remote_type = "remote"
            elif "hybrid" in location_lower or "hybride" in location_lower:
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
            "description": None,
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "EUR",
            "job_type": None,
            "experience_level": None,
            "skills": [],
            "benefits": [],
        }
