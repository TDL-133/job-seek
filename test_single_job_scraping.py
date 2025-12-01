"""
Display the complete result of scraping a single job offer with Firecrawl
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")


async def scrape_and_parse_job():
    """Scrape a job page and show what we get"""
    
    # URL d'une vraie offre Indeed
    job_url = "https://www.indeed.com/jobs?q=Product+Manager&l=Paris"
    
    print("="*80)
    print("🔍 SCRAPING JOB OFFER WITH FIRECRAWL")
    print("="*80)
    print(f"URL: {job_url}\n")
    
    # 1. Call Firecrawl
    print("📡 Calling Firecrawl API...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "url": job_url,
                "formats": ["html", "markdown"],
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Firecrawl failed: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        # 2. Show Firecrawl response structure
        print(f"✅ Firecrawl response received\n")
        print("📦 Response structure:")
        print(f"  - success: {data.get('success')}")
        print(f"  - data keys: {list(data.get('data', {}).keys())}")
        
        actual_data = data.get("data", {})
        html = actual_data.get("html", "")
        markdown = actual_data.get("markdown", "")
        metadata = actual_data.get("metadata", {})
        
        print(f"\n📊 Content sizes:")
        print(f"  - HTML: {len(html):,} characters")
        print(f"  - Markdown: {len(markdown):,} characters")
        
        print(f"\n📋 Metadata:")
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  - {key}: {value[:100]}...")
            else:
                print(f"  - {key}: {value}")
        
        # 3. Parse HTML with BeautifulSoup to find jobs
        print(f"\n🔍 Parsing HTML to extract job offers...")
        soup = BeautifulSoup(html, "lxml")
        
        # Try Indeed selectors
        job_cards = soup.find_all("div", class_="job_seen_beacon")[:3]
        if not job_cards:
            job_cards = soup.find_all("div", {"data-testid": "slider_item"})[:3]
        
        print(f"Found {len(job_cards)} job cards\n")
        
        # 4. Show parsed jobs
        if job_cards:
            for i, card in enumerate(job_cards, 1):
                print(f"{'='*80}")
                print(f"JOB #{i}")
                print('='*80)
                
                # Extract fields
                title_elem = (
                    card.find("h2", class_="jobTitle") or 
                    card.find("span", {"data-testid": "jobTitle"})
                )
                company_elem = (
                    card.find("span", {"data-testid": "company-name"}) or
                    card.find("span", class_="companyName")
                )
                location_elem = (
                    card.find("div", {"data-testid": "text-location"}) or
                    card.find("div", class_="companyLocation")
                )
                salary_elem = card.find("div", class_="salary-snippet-container")
                
                # Display
                if title_elem:
                    print(f"📌 Title: {title_elem.get_text(strip=True)}")
                if company_elem:
                    print(f"🏢 Company: {company_elem.get_text(strip=True)}")
                if location_elem:
                    print(f"📍 Location: {location_elem.get_text(strip=True)}")
                if salary_elem:
                    print(f"💰 Salary: {salary_elem.get_text(strip=True)}")
                
                # Get job URL
                link_elem = card.find("a", href=True)
                if link_elem:
                    href = link_elem.get("href", "")
                    if href.startswith("/"):
                        job_url = f"https://www.indeed.com{href}"
                    else:
                        job_url = href
                    print(f"🔗 URL: {job_url[:80]}...")
                
                # Show raw HTML snippet
                print(f"\n📄 Raw HTML snippet (first 500 chars):")
                print(str(card)[:500])
                print("...")
                print()
        else:
            print("⚠️  No job cards found with current selectors")
            print("\n📄 First 2000 chars of HTML:")
            print(html[:2000])
            print("...")
        
        # 5. Show markdown preview
        if markdown:
            print(f"\n{'='*80}")
            print("📝 MARKDOWN PREVIEW (first 1000 chars)")
            print('='*80)
            print(markdown[:1000])
            print("...")


if __name__ == "__main__":
    asyncio.run(scrape_and_parse_job())
