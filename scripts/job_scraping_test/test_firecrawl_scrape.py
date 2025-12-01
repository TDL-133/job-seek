#!/usr/bin/env python3
"""
Test Firecrawl scraping of Indeed search result pages to extract individual job URLs.

This script:
1. Uses Firecrawl Search to find Indeed search result pages for Lyon
2. Uses Firecrawl Scrape to extract job URLs from those pages
3. Reports final job postings found
"""
import asyncio
import os
import re
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/.env")
load_dotenv(env_path)

async def firecrawl_search(api_key: str, query: str, limit: int = 5):
    """Step 1: Search for Indeed pages."""
    print(f"\n🔎 STEP 1: Searching Indeed with Firecrawl...")
    print(f"   Query: {query}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": query,
                    "limit": limit,
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("data", [])
                urls = [r.get("url") for r in results if r.get("url")]
                print(f"   ✅ Found {len(urls)} search result pages")
                return urls
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                return []
                
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return []

async def firecrawl_scrape_page(api_key: str, url: str):
    """Step 2: Scrape a single Indeed search page to extract job URLs."""
    print(f"\n🔍 STEP 2: Scraping page {url[:60]}...")
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "formats": ["markdown", "html"],
                    "onlyMainContent": False  # Need full page to get job links
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("data", {})
                
                # Extract job URLs from markdown and HTML
                markdown = content.get("markdown", "")
                html = content.get("html", "")
                
                # Pattern for Indeed job URLs
                # Examples: /viewjob?jk=abc123, /rc/clk?jk=def456, /company/xyz/jobs/title-123
                job_patterns = [
                    r'https://fr\.indeed\.com/(?:rc/clk\?jk=|viewjob\?jk=|pagead/clk\?id=)([a-zA-Z0-9]+)',
                    r'href=["\']([^"\']*(?:/viewjob\?jk=|/rc/clk\?jk=)[^"\']*)["\']',
                    r'(/company/[^/]+/jobs/[^\s\'"]+)'
                ]
                
                job_urls = set()
                for pattern in job_patterns:
                    matches = re.findall(pattern, markdown + " " + html)
                    for match in matches:
                        if match.startswith('http'):
                            job_urls.add(match)
                        elif match.startswith('/'):
                            job_urls.add(f"https://fr.indeed.com{match}")
                        else:
                            # Job ID only, construct full URL
                            job_urls.add(f"https://fr.indeed.com/viewjob?jk={match}")
                
                # Filter out search pages and duplicates
                filtered_urls = []
                for url in job_urls:
                    # Skip if it's another search page
                    if '/q-' in url and '-emplois.html' in url:
                        continue
                    # Skip if it's a company overview page without job ID
                    if '/cmp/' in url and '/jobs/' not in url:
                        continue
                    filtered_urls.append(url)
                
                print(f"   ✅ Extracted {len(filtered_urls)} job URLs from this page")
                return filtered_urls
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                return []
                
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return []

async def main():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    print(f"🔑 Using Firecrawl key ending in: ...{api_key[-5:] if api_key else 'NONE'}")
    
    if not api_key:
        print("❌ No API Key found!")
        return

    job_title = "Product Manager"
    city = "Lyon"
    region = "Auvergne-Rhône-Alpes"
    
    # Step 1: Search for Indeed pages
    query = f"{job_title} {city} {region} site:fr.indeed.com"
    search_pages = await firecrawl_search(api_key, query, limit=3)  # Limit to 3 pages to save credits
    
    if not search_pages:
        print("\n❌ No search pages found!")
        return
    
    # Step 2: Scrape each page to extract job URLs
    print("\n" + "="*80)
    all_job_urls = []
    for page_url in search_pages:
        job_urls = await firecrawl_scrape_page(api_key, page_url)
        all_job_urls.extend(job_urls)
        await asyncio.sleep(1)  # Rate limiting
    
    # Deduplicate
    unique_jobs = list(set(all_job_urls))
    
    # Filter by Lyon location (in URL)
    lyon_jobs = [url for url in unique_jobs if 'lyon' in url.lower()]
    
    print("\n" + "="*80)
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Total job URLs extracted: {len(unique_jobs)}")
    print(f"   Jobs matching Lyon: {len(lyon_jobs)}")
    
    print(f"\n📋 Lyon Job URLs:")
    for i, url in enumerate(lyon_jobs[:10], 1):  # Show first 10
        print(f"   {i}. {url}")
    
    if len(lyon_jobs) > 10:
        print(f"   ... and {len(lyon_jobs) - 10} more")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(main())
