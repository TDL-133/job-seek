#!/usr/bin/env python3
"""
Test Indeed Direct Search Page Scraping using Firecrawl
"""
import asyncio
import os
import re
import httpx
from urllib.parse import quote
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def test_indeed_scrape():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("No API key")
        return

    job_title = "Customer Success Manager"
    city = "Marseille"
    
    # Construct Indeed Search URL
    query_encoded = quote(job_title)
    loc_encoded = quote(city)
    url = f"https://fr.indeed.com/jobs?q={query_encoded}&l={loc_encoded}"
    
    print(f"🔥 Scraping Indeed Search URL: {url}")
    
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
                "waitFor": 5000
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            html = data.get("data", {}).get("html", "")
            
            print(f"✅ Scrape successful. HTML length: {len(html)}")
            
            # Extract job links
            # Indeed Patterns:
            # /viewjob?jk=...
            # /rc/clk?jk=...
            # /company/.../jobs/...
            
            matches = re.findall(r'href=["\']([^"\']*(?:/viewjob\?jk=|/rc/clk\?jk=|/company/[^/]+/jobs/)[^"\']*)["\']', html)
            
            # Track job IDs to deduplicate
            job_ids = set()
            urls = []
            
            for match in matches:
                if match.startswith('/'):
                    match = f"https://fr.indeed.com{match}"
                
                # Extract JK (Job ID)
                jk_match = re.search(r'jk=([a-f0-9]+)', match)
                if jk_match:
                    jk = jk_match.group(1)
                    if jk in job_ids:
                        continue
                    job_ids.add(jk)
                    urls.append(match)
                elif '/company/' in match and '/jobs/' in match:
                    urls.append(match)
            
            print(f"📊 Found {len(urls)} unique job URLs:")
            for url in urls[:10]:
                print(f"   - {url}")
            if len(urls) > 10:
                print(f"   ... and {len(urls)-10} more")
                
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_indeed_scrape())
