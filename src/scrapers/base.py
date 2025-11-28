from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
import re


class BaseScraper(ABC):
    """Base class for job scrapers."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.platform_name = "base"
    
    @abstractmethod
    async def search(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search for jobs on the platform."""
        pass
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page and return its HTML content."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None
    
    def parse_salary(self, salary_text: str) -> Dict:
        """Parse salary text into min/max values."""
        result = {"min": None, "max": None, "currency": "EUR"}
        
        if not salary_text:
            return result
        
        # Clean the text
        salary_text = salary_text.replace(",", "").replace(" ", "")
        
        # Detect currency
        if "$" in salary_text:
            result["currency"] = "USD"
        elif "£" in salary_text:
            result["currency"] = "GBP"
        elif "€" in salary_text:
            result["currency"] = "EUR"
        
        # Extract numbers
        numbers = re.findall(r"\d+(?:\.\d+)?", salary_text)
        numbers = [float(n) for n in numbers]
        
        # Handle K notation (e.g., 50K)
        if "k" in salary_text.lower():
            numbers = [n * 1000 if n < 1000 else n for n in numbers]
        
        if len(numbers) >= 2:
            result["min"] = min(numbers)
            result["max"] = max(numbers)
        elif len(numbers) == 1:
            result["min"] = numbers[0]
            result["max"] = numbers[0]
        
        return result
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract common skills from job description."""
        common_skills = [
            "python", "javascript", "typescript", "react", "node.js", "nodejs",
            "java", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "git", "ci/cd", "agile", "scrum", "rest", "graphql", "api",
            "machine learning", "ml", "ai", "data science", "deep learning",
            "html", "css", "sass", "webpack", "vue", "angular", "svelte",
            "django", "flask", "fastapi", "spring", "express", "nest.js",
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))
