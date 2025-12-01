#!/usr/bin/env python3
"""
Test WTTJ Search Page Scraping using Firecrawl
"""
import asyncio
import os
import re
import json
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def test_wttj_scrape():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("No API key")
        return

    # Construct WTTJ Search URL
    # Query: Customer Success Manager, Marseille
    url = "https://www.welcometothejungle.com/fr/jobs?query=Customer%20Success%20Manager&aroundQuery=Marseille"
    
    print(f"🔥 Scraping WTTJ Search URL: {url}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "url": url,
                "formats": ["html", "markdown"],
                "onlyMainContent": False,
                "waitFor": 5000  # Wait for SPA to render
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            html = data.get("data", {}).get("html", "")
            
            print(f"✅ Scrape successful. HTML length: {len(html)}")
            
            # Extract job links
            # Pattern: /companies/{company}/jobs/{slug}
            # Full URL or relative
            
            matches = re.findall(r'href=["\']([^"\']*/companies/[^"\'/]+/jobs/[^"\']*)["\']', html)
            
            job_urls = set()
            for match in matches:
                if match.startswith('/'):
                    match = f"https://www.welcometothejungle.com{match}"
                job_urls.add(match)
            
            print(f"📊 Found {len(job_urls)} unique job URLs:")
            for url in job_urls:
                print(f"   - {url}")
                
            # Save html for inspection if needed
            # with open("wttj_debug.html", "w") as f:
            #     f.write(html)
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_wttj_scrape())
