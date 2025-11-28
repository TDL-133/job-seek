"""
Centralized scraping service with fallback mechanism.

Uses Firecrawl and BrightData APIs for reliable web scraping,
with httpx as fallback.
"""
from typing import Optional
import httpx
import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ScrapingMethod(str, Enum):
    """Scraping methods available."""
    FIRECRAWL = "firecrawl"
    BRIGHTDATA = "brightdata"
    HTTPX = "httpx"


class ScrapingService:
    """Service for fetching web pages with multiple fallback strategies."""
    
    def __init__(self):
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        self.brightdata_api_key = os.getenv("BRIGHTDATA_API_KEY")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with fallback strategy.
        
        Tries methods in order:
        1. Firecrawl (fast, bypass anti-bot)
        2. BrightData (slower but powerful with proxies)
        3. httpx (simple fallback)
        
        Args:
            url: Target URL to scrape
            
        Returns:
            HTML content or None if all methods fail
        """
        # Try Firecrawl first (fastest, most reliable)
        if self.firecrawl_api_key:
            html = await self._fetch_with_firecrawl(url)
            if html:
                logger.info(f"Successfully scraped {url} with Firecrawl")
                return html
            logger.warning(f"Firecrawl failed for {url}, trying BrightData")
        
        # Try BrightData (powerful but slower)
        if self.brightdata_api_key:
            html = await self._fetch_with_brightdata(url)
            if html:
                logger.info(f"Successfully scraped {url} with BrightData")
                return html
            logger.warning(f"BrightData failed for {url}, trying httpx fallback")
        
        # Fallback to simple httpx
        html = await self._fetch_with_httpx(url)
        if html:
            logger.info(f"Successfully scraped {url} with httpx")
            return html
        
        logger.error(f"All scraping methods failed for {url}")
        return None
    
    async def _fetch_with_firecrawl(self, url: str) -> Optional[str]:
        """
        Fetch page using Firecrawl API.
        
        Firecrawl is a professional scraping service that bypasses anti-bot measures.
        Free tier: 500 requests/month
        Docs: https://docs.firecrawl.dev/
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {self.firecrawl_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "url": url,
                        "formats": ["html"],
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("html")
                else:
                    logger.warning(f"Firecrawl returned status {response.status_code} for {url}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Firecrawl error for {url}: {e}")
            return None
    
    async def _fetch_with_brightdata(self, url: str) -> Optional[str]:
        """
        Fetch page using BrightData Scraper API.
        
        BrightData (formerly Luminati) provides professional web scraping with:
        - Rotating residential proxies
        - CAPTCHA handling
        - JavaScript rendering
        
        Using ScraperAPI endpoint for simplicity.
        Docs: https://docs.brightdata.com/
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "http://api.scraperapi.com/",
                    params={
                        "api_key": self.brightdata_api_key,
                        "url": url,
                        "render": "false",  # Set to "true" if JS rendering needed
                    }
                )
                
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"BrightData returned status {response.status_code} for {url}")
                    return None
                    
        except Exception as e:
            logger.warning(f"BrightData error for {url}: {e}")
            return None
    
    async def _fetch_with_httpx(self, url: str) -> Optional[str]:
        """
        Fetch page using simple httpx request.
        
        This is the fallback method when paid services are unavailable.
        May be blocked by anti-bot measures.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url, 
                    headers=self.headers, 
                    follow_redirects=True
                )
                response.raise_for_status()
                return response.text
                
        except Exception as e:
            logger.warning(f"httpx error for {url}: {e}")
            return None
