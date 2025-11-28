from typing import List, Dict, Optional
from urllib.parse import quote_plus
from .base import BaseScraper
from bs4 import BeautifulSoup


class GlassdoorScraper(BaseScraper):
    """
    Glassdoor job scraper.
    
    Note: Glassdoor has strong anti-scraping measures. For production use,
    consider using MCP tools (playwright, firecrawl) for more reliable access.
    """
    
    def __init__(self):
        super().__init__()
        self.platform_name = "glassdoor"
        self.base_url = "https://www.glassdoor.com/Job/jobs.htm"
    
    async def search(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search Glassdoor for jobs.
        
        For better results, use MCP tools (firecrawl, playwright) configured
        in your environment for enhanced scraping capabilities.
        """
        jobs = []
        
        # Build search URL
        params = [f"sc.keyword={quote_plus(keywords)}"]
        
        if location:
            params.append(f"locT=C&locId=0&locKeyword={quote_plus(location)}")
        
        if remote_only:
            params.append("remoteWorkType=1")
        
        url = f"{self.base_url}?{'&'.join(params)}"
        
        html = await self.fetch_page(url)
        if not html:
            return jobs
        
        soup = BeautifulSoup(html, "lxml")
        
        # Parse job cards - Glassdoor uses various class names
        job_cards = soup.find_all("li", class_="react-job-listing")[:limit]
        
        if not job_cards:
            # Try alternative selector
            job_cards = soup.find_all("div", {"data-test": "jobListing"})[:limit]
        
        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"Error parsing Glassdoor job card: {e}")
                continue
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a Glassdoor job card."""
        title_elem = card.find("a", {"data-test": "job-link"})
        company_elem = card.find("div", {"data-test": "employer-short-name"})
        location_elem = card.find("span", {"data-test": "emp-location"})
        salary_elem = card.find("span", {"data-test": "detailSalary"})
        rating_elem = card.find("span", {"data-test": "rating"})
        
        if not title_elem:
            # Try alternative selectors
            title_elem = card.find("a", class_="jobLink")
        
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.get_text())
        company_name = self.clean_text(company_elem.get_text()) if company_elem else None
        location = self.clean_text(location_elem.get_text()) if location_elem else None
        
        # Get job URL
        job_url = title_elem.get("href", "")
        if job_url and not job_url.startswith("http"):
            job_url = f"https://www.glassdoor.com{job_url}"
        
        # Parse salary
        salary_info = {"min": None, "max": None, "currency": "EUR"}
        if salary_elem:
            salary_text = salary_elem.get_text()
            salary_info = self.parse_salary(salary_text)
        
        # Get company rating
        company_rating = None
        if rating_elem:
            try:
                company_rating = float(rating_elem.get_text())
            except:
                pass
        
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
            "description": None,
            "salary_min": salary_info["min"],
            "salary_max": salary_info["max"],
            "salary_currency": salary_info["currency"],
            "job_type": None,
            "experience_level": None,
            "skills": [],
            "benefits": [],
            "company_rating": company_rating,
        }
