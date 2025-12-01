#!/usr/bin/env python3
"""
Test Glassdoor Direct Search Page Scraping using Firecrawl
"""
import asyncio
import os
import re
import httpx
from urllib.parse import quote
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def test_glassdoor_scrape():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("No API key")
        return

    job_title = "Customer Success Manager"
    city = "Marseille"
    
    # Construct Glassdoor Search URL
    query_encoded = quote(job_title)
    loc_encoded = quote(city)
    # Using .fr domain as requested
    url = f"https://www.glassdoor.fr/Job/jobs.htm?sc.keyword={query_encoded}&locKeyword={loc_encoded}"
    
    print(f"🔥 Scraping Glassdoor Search URL: {url}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "url": url,
                "formats": ["html"],
                "onlyMainContent": False,
                # Glassdoor often needs some wait time or specialized handling
                "waitFor": 5000
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            html = data.get("data", {}).get("html", "")
            
            print(f"✅ Scrape successful. HTML length: {len(html)}")
            
            # Extract job links
            # Looking for: /partner/url/... or /job-listing/...
            
            # Regex 1: /partner/url/
            matches = re.findall(r'href=["\']([^"\']*(?:/partner/url/|/job-listing/)[^"\']*)["\']', html)
            
            job_urls = set()
            for match in matches:
                if match.startswith('/'):
                    match = f"https://www.glassdoor.fr{match}"
                job_urls.add(match)
            
            print(f"📊 Found {len(job_urls)} unique job URLs:")
            for url in list(job_urls)[:10]:
                print(f"   - {url}")
            if len(job_urls) > 10:
                print(f"   ... and {len(job_urls)-10} more")
                
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_glassdoor_scrape())
