from typing import List, Dict, Optional
from urllib.parse import quote_plus
from .base import BaseScraper
from bs4 import BeautifulSoup


class IndeedScraper(BaseScraper):
    """Indeed job scraper."""
    
    def __init__(self):
        super().__init__()
        self.platform_name = "indeed"
        self.base_url = "https://www.indeed.com/jobs"
    
    async def search(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search Indeed for jobs.
        
        For better results, use MCP tools (firecrawl, playwright) configured
        in your environment for enhanced scraping capabilities.
        """
        jobs = []
        
        # Build search URL
        params = [f"q={quote_plus(keywords)}"]
        
        if location:
            params.append(f"l={quote_plus(location)}")
        
        if remote_only:
            params.append("remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11")
        
        # Experience level filter
        exp_mapping = {
            "entry": "entry_level",
            "mid": "mid_level",
            "senior": "senior_level"
        }
        if experience_level and experience_level.lower() in exp_mapping:
            params.append(f"explvl={exp_mapping[experience_level.lower()]}")
        
        url = f"{self.base_url}?{'&'.join(params)}"
        
        html = await self.fetch_page(url)
        if not html:
            return jobs
        
        soup = BeautifulSoup(html, "lxml")
        
        # Parse job cards
        job_cards = soup.find_all("div", class_="job_seen_beacon")[:limit]
        
        if not job_cards:
            # Try alternative selectors
            job_cards = soup.find_all("div", {"data-testid": "slider_item"})[:limit]
        
        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"Error parsing Indeed job card: {e}")
                continue
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse an Indeed job card."""
        # Try multiple selectors for title
        title_elem = (
            card.find("h2", class_="jobTitle") or 
            card.find("span", {"data-testid": "jobTitle"}) or
            card.find("a", {"data-jk": True})
        )
        
        company_elem = (
            card.find("span", {"data-testid": "company-name"}) or
            card.find("span", class_="companyName")
        )
        
        location_elem = (
            card.find("div", {"data-testid": "text-location"}) or
            card.find("div", class_="companyLocation")
        )
        
        salary_elem = (
            card.find("div", {"data-testid": "attribute_snippet_testid"}) or
            card.find("div", class_="salary-snippet-container")
        )
        
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.get_text())
        company_name = self.clean_text(company_elem.get_text()) if company_elem else None
        location = self.clean_text(location_elem.get_text()) if location_elem else None
        
        # Get job URL
        link_elem = card.find("a", href=True)
        job_url = ""
        if link_elem:
            href = link_elem.get("href", "")
            if href.startswith("/"):
                job_url = f"https://www.indeed.com{href}"
            else:
                job_url = href
        
        # Parse salary
        salary_info = {"min": None, "max": None, "currency": "EUR"}
        if salary_elem:
            salary_text = salary_elem.get_text()
            salary_info = self.parse_salary(salary_text)
        
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
        }
