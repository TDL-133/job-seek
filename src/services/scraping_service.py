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
    PARALLEL = "parallel"
    FIRECRAWL = "firecrawl"
    BRIGHTDATA = "brightdata"
    HTTPX = "httpx"


class ScrapingService:
    """Service for fetching web pages with multiple fallback strategies."""
    
    def __init__(self):
        self.parallel_api_key = os.getenv("PARALLEL_API_KEY")
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        self.brightdata_api_key = os.getenv("BRIGHTDATA_API_KEY")
        self.brightdata_mcp_url = os.getenv("BRIGHTDATA_MCP_URL", "https://mcp.brightdata.com/sse")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with fallback strategy.
        
        Tries methods in order:
        1. Parallel Search (fast, AI-powered extraction)
        2. Firecrawl (fast, bypass anti-bot)
        3. BrightData (slower but powerful with proxies)
        4. httpx (simple fallback)
        
        Args:
            url: Target URL to scrape
            
        Returns:
            HTML content or None if all methods fail
        """
        # Try Parallel Search first (AI-powered, agentic mode)
        if self.parallel_api_key:
            html = await self._fetch_with_parallel(url)
            if html:
                logger.info(f"Successfully scraped {url} with Parallel Search")
                return html
            logger.warning(f"Parallel Search failed for {url}, trying Firecrawl")
        
        # Try Firecrawl (fastest, most reliable)
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
                    # Firecrawl V1 API returns data in nested structure
                    if data.get("success"):
                        actual_data = data.get("data", {})
                        html = actual_data.get("html", "")
                        if html:
                            return html
                        else:
                            logger.warning(f"Firecrawl returned success but no HTML for {url}")
                            return None
                    else:
                        logger.warning(f"Firecrawl returned success=false for {url}. Response: {data}")
                        return None
                else:
                    logger.warning(f"Firecrawl returned status {response.status_code} for {url}")
                    try:
                        error_data = response.json()
                        logger.warning(f"Firecrawl error details: {error_data}")
                    except:
                        logger.warning(f"Firecrawl response text: {response.text[:500]}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Firecrawl error for {url}: {type(e).__name__}: {e}")
            return None
    
    async def _fetch_with_parallel(self, url: str) -> Optional[str]:
        """
        Fetch page using Parallel Search MCP Server.
        
        Parallel Search MCP provides AI-powered web content extraction with:
        - Real-time web search and content retrieval
        - web_fetch tool for extracting content from specific URLs
        - Automatic anti-bot bypass and CAPTCHA handling
        - Fast response times with intelligent caching
        
        MCP Endpoint: https://search-mcp.parallel.ai/mcp
        Docs: https://docs.parallel.ai/integrations/mcp/search-mcp
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Use MCP JSON-RPC protocol to call web_fetch tool
                response = await client.post(
                    "https://search-mcp.parallel.ai/mcp",
                    headers={
                        "Authorization": f"Bearer {self.parallel_api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": "web_fetch",
                            "arguments": {
                                "urls": [url],  # web_fetch expects array of URLs
                            }
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # MCP returns result in JSON-RPC format
                    if "result" in data:
                        result = data["result"]
                        # Extract content from MCP tool result
                        if isinstance(result, dict):
                            content = result.get("content") or result.get("html") or result.get("text")
                            if isinstance(content, list) and len(content) > 0:
                                # MCP often returns array of content blocks
                                content = content[0].get("text") if isinstance(content[0], dict) else str(content[0])
                            if content:
                                return str(content)
                        logger.warning(f"Parallel Search MCP returned result but no content for {url}. Result: {result}")
                        return None
                    elif "error" in data:
                        logger.warning(f"Parallel Search MCP returned error for {url}: {data['error']}")
                        return None
                    else:
                        logger.warning(f"Parallel Search MCP unexpected response format for {url}. Response: {data}")
                        return None
                else:
                    logger.warning(f"Parallel Search MCP returned status {response.status_code} for {url}")
                    try:
                        error_data = response.json()
                        logger.warning(f"Parallel Search MCP error: {error_data}")
                    except:
                        logger.warning(f"Parallel Search MCP response: {response.text[:500]}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Parallel Search MCP error for {url}: {type(e).__name__}: {e}")
            return None
    
    async def _fetch_with_brightdata(self, url: str) -> Optional[str]:
        """
        Fetch page using BrightData MCP Server.
        
        BrightData MCP provides web scraping through SSE endpoint with:
        - Rotating residential proxies
        - CAPTCHA handling  
        - JavaScript rendering
        - Bot detection bypass
        
        Using MCP SSE endpoint: https://mcp.brightdata.com/sse
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # BrightData MCP uses POST with URL and token
                response = await client.post(
                    self.brightdata_mcp_url,
                    params={
                        "token": self.brightdata_api_key,
                    },
                    json={
                        "method": "scrape_as_markdown",
                        "params": {
                            "url": url,
                        }
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                )
                
                if response.status_code == 200:
                    # MCP returns JSON with result
                    data = response.json()
                    # Extract HTML/markdown from MCP response
                    if isinstance(data, dict):
                        html = data.get("content") or data.get("html") or data.get("result")
                        if html:
                            return html
                    # If direct text response
                    return response.text
                else:
                    logger.warning(f"BrightData MCP returned status {response.status_code} for {url}")
                    if response.status_code != 401:
                        logger.debug(f"BrightData response: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            logger.warning(f"BrightData MCP error for {url}: {type(e).__name__}: {e}")
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
