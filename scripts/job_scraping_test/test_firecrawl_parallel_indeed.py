#!/usr/bin/env python3
"""
Isolated test: Firecrawl 2-step Indeed search + Parallel Extract.

This script tests ONLY:
1. Firecrawl Search → Find Indeed search result pages
2. Firecrawl Scrape → Extract job URLs from those pages
3. Parallel Extract → Extract content from job URLs
4. Export structured CSV

No other sources (Glassdoor, WTTJ, LinkedIn) are involved.
"""
import asyncio
import csv
import json
import os
import re
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load environment variables
env_path = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/.env")
load_dotenv(env_path)

# Configuration
JOB_TITLE = "Product Manager"
CITY = "Lyon"
REGION = "Auvergne-Rhône-Alpes"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

async def firecrawl_step1_search(api_key: str):
    """Step 1: Search for Indeed search result pages."""
    query = f"{JOB_TITLE} {CITY} {REGION} site:fr.indeed.com"
    print(f"\n🔥 STEP 1/3: Firecrawl Search")
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
                    "limit": 3,  # Get 3 search pages
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                pages = [r.get("url") for r in data.get("data", []) if r.get("url")]
                print(f"   ✅ Found {len(pages)} Indeed search pages")
                
                # Save
                with open(RESULTS_DIR / "firecrawl_step1_search.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                return pages
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                return []
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return []

async def firecrawl_step2_extract_urls(api_key: str, search_pages: list):
    """Step 2: Scrape each search page to extract job URLs."""
    print(f"\n🔥 STEP 2/3: Firecrawl Scrape (extract job URLs)")
    all_job_urls = []
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        for i, page_url in enumerate(search_pages, 1):
            print(f"   [{i}/{len(search_pages)}] Scraping {page_url[:50]}...")
            
            try:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": page_url,
                        "formats": ["markdown", "html"],
                        "onlyMainContent": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("data", {})
                    markdown = content.get("markdown", "")
                    html = content.get("html", "")
                    
                    # Extract job URLs with regex
                    patterns = [
                        r'https://fr\.indeed\.com/(?:rc/clk\?jk=|viewjob\?jk=|pagead/clk\?id=)([a-zA-Z0-9]+)',
                        r'href=["\']([^"\']*(?:/viewjob\?jk=|/rc/clk\?jk=)[^"\']*)["\']',
                        r'(/company/[^/]+/jobs/[^\s\'"]+)'
                    ]
                    
                    page_jobs = set()
                    for pattern in patterns:
                        matches = re.findall(pattern, markdown + " " + html)
                        for match in matches:
                            if match.startswith('http'):
                                page_jobs.add(match)
                            elif match.startswith('/'):
                                page_jobs.add(f"https://fr.indeed.com{match}")
                            else:
                                page_jobs.add(f"https://fr.indeed.com/viewjob?jk={match}")
                    
                    # Filter out search pages
                    for url in page_jobs:
                        if '/q-' in url and '-emplois.html' in url:
                            continue
                        if '/cmp/' in url and '/jobs/' not in url:
                            continue
                        all_job_urls.append(url)
                    
                    print(f"      ✓ Extracted {len(page_jobs)} URLs")
                else:
                    print(f"      ❌ Error {response.status_code}")
            
            except Exception as e:
                print(f"      ❌ Exception: {e}")
            
            await asyncio.sleep(0.5)  # Rate limiting
    
    unique_urls = list(set(all_job_urls))
    print(f"   ✅ Total unique job URLs: {len(unique_urls)}")
    
    # Save
    with open(RESULTS_DIR / "firecrawl_step2_urls.json", "w") as f:
        json.dump({"search_pages": search_pages, "job_urls": unique_urls}, f, indent=2)
    
    return unique_urls

async def parallel_extract(api_key: str, job_urls: list):
    """Step 3: Extract content from all job URLs using Parallel Extract API."""
    print(f"\n📡 STEP 3/3: Parallel Extract API")
    print(f"   Extracting content from {len(job_urls)} URLs...")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:  # 3 min for 50 URLs
            response = await client.post(
                "https://api.parallel.ai/v1beta/extract",
                headers={
                    "x-api-key": api_key,
                    "parallel-beta": "search-extract-2025-10-10",
                    "Content-Type": "application/json"
                },
                json={
                    "urls": job_urls,
                    "objective": "Extract job posting details: title, company name, location, salary range, contract type (CDI/CDD/Stage), remote work policy, full description, required skills, posting date",
                    "excerpts": True,
                    "full_content": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Extracted {len(data.get('results', []))} pages")
                
                # Save
                with open(RESULTS_DIR / "parallel_extract.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                return data
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def structure_jobs(extract_data):
    """Parse extracted data into structured format with improved location filtering."""
    print(f"\n📊 Structuring job data...")
    jobs = []
    skipped_count = 0
    
    for result in extract_data.get("results", []):
        url = result.get("url", "")
        
        # Combine content
        content = ""
        if result.get("excerpts"):
            content += " ".join(result["excerpts"])
        if result.get("full_content"):
            content += " " + result["full_content"]
        
        if not content:
            continue
        
        # Clean HTML entities and tags from content
        import html
        content = html.unescape(content)
        content = re.sub(r'<[^>]+>', ' ', content)  # Remove HTML tags
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        
        # Extract title
        title = result.get("title", "Unknown Title")
        if not title or title == "Unknown Title":
            # Try to extract from content
            title_match = re.search(r'^([A-Z][^\n]{10,80})', content)
            if title_match:
                title = title_match.group(1).strip()
        
        # IMPROVED location extraction with multiple strategies
        location = None
        content_lower = content.lower()
        
        # Strategy 1: Look for explicit location markers
        location_patterns = [
            r"(?:lieu|location|localisation|ville)\s*[:\-]\s*([^\n\.;]{3,50})",
            r"(?:à|in)\s+(Lyon|Paris|Bordeaux|Marseille|Toulouse|Nantes|Nice|Grenoble|Strasbourg|Rennes|Lille)[,\s\.]?",
            r"(Lyon|Paris|Bordeaux|Marseille|Toulouse|Nantes|Nice|Grenoble|Strasbourg|Rennes|Lille)\s*(?:\([0-9]{2}\)|,|\.|$)",
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                location_candidate = match.group(1).strip()
                # Clean up location
                location_candidate = re.sub(r'\s+', ' ', location_candidate)
                location_candidate = location_candidate.split('.')[0].split(';')[0]
                if len(location_candidate) < 100:  # Sanity check
                    location = location_candidate
                    break
        
        # Strategy 2: Detect major French cities in content
        if not location:
            major_cities = ['Lyon', 'Paris', 'Bordeaux', 'Marseille', 'Toulouse', 'Nantes', 'Nice', 'Grenoble', 'Strasbourg', 'Rennes', 'Lille']
            for city in major_cities:
                if city.lower() in content_lower:
                    location = city
                    break
        
        # CRITICAL: Filter out jobs NOT in target city (Lyon)
        target_city = CITY.lower()  # "lyon"
        
        if location:
            location_lower = location.lower()
            
            # Check if target city is in location
            if target_city not in location_lower:
                # Skip this job - wrong location
                skipped_count += 1
                print(f"   ⊗ Skipped (wrong location): {title[:40]}... in {location}")
                continue
        else:
            # No location found - skip to be safe
            skipped_count += 1
            print(f"   ⊗ Skipped (no location): {title[:40]}...")
            continue
        
        # Extract company
        company = "Indeed Listing"
        company_patterns = [
            r"(?:entreprise|company|société)\s*[:\-]\s*([^\n\.;]{3,50})",
            r"chez\s+([A-Z][^\n\.;]{2,40})",
        ]
        for pattern in company_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                break
        
        # Extract contract type
        contract_type = "Not specified"
        if "cdi" in content_lower:
            contract_type = "CDI"
        elif "cdd" in content_lower:
            contract_type = "CDD"
        elif "stage" in content_lower or "internship" in content_lower:
            contract_type = "Stage"
        elif "alternance" in content_lower:
            contract_type = "Alternance"
        
        # Extract remote policy
        remote = "Not specified"
        if "full remote" in content_lower or "100% remote" in content_lower or "télétravail complet" in content_lower:
            remote = "Remote"
        elif "hybrid" in content_lower or "hybride" in content_lower or "télétravail partiel" in content_lower:
            remote = "Hybrid"
        elif "on-site" in content_lower or "sur site" in content_lower or "présentiel" in content_lower:
            remote = "Onsite"
        elif "télétravail" in content_lower or "remote" in content_lower:
            remote = "Remote/Hybrid"
        
        job = {
            "title": title,
            "company": company,
            "location": location,
            "salary": "Not specified",
            "contract_type": contract_type,
            "remote": remote,
            "description": content[:200] + "...",
            "skills": "",
            "posted_date": "Not specified",
            "url": url,
            "source": "indeed",
            "extraction_method": "firecrawl+parallel"
        }
        
        jobs.append(job)
        print(f"   ✅ {job['title'][:50]} @ {location}")
    
    print(f"\n   📊 Kept {len(jobs)} jobs matching {CITY}")
    print(f"   ⊗ Filtered out {skipped_count} jobs (wrong/no location)")
    
    return jobs

def export_csv(jobs):
    """Export jobs to CSV."""
    csv_path = RESULTS_DIR / "indeed_jobs.csv"
    
    fieldnames = [
        "title", "company", "location", "salary", "contract_type",
        "remote", "description", "skills", "posted_date",
        "url", "source", "extraction_method"
    ]
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs)
    
    print(f"\n✅ CSV exported: {csv_path}")
    return csv_path

async def main():
    print("="*80)
    print("🔥 TEST: Firecrawl 2-Step Indeed + Parallel Extract")
    print(f"🎯 Search: {JOB_TITLE} in {CITY}, {REGION}")
    print("="*80)
    
    # Get API keys
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    parallel_key = os.getenv("PARALLEL_API_KEY")
    
    if not firecrawl_key:
        print("❌ FIRECRAWL_API_KEY not found in .env")
        return
    if not parallel_key:
        print("❌ PARALLEL_API_KEY not found in .env")
        return
    
    print(f"🔑 Firecrawl key: ...{firecrawl_key[-5:]}")
    print(f"🔑 Parallel key: ...{parallel_key[-5:]}")
    
    # Step 1: Search for Indeed pages
    search_pages = await firecrawl_step1_search(firecrawl_key)
    if not search_pages:
        print("\n❌ No search pages found. Aborting.")
        return
    
    # Step 2: Extract job URLs from pages
    job_urls = await firecrawl_step2_extract_urls(firecrawl_key, search_pages)
    if not job_urls:
        print("\n❌ No job URLs found. Aborting.")
        return
    
    # Limit to 50 URLs (Parallel Extract API max)
    if len(job_urls) > 50:
        print(f"\n⚠️  Limiting to 50 URLs (Parallel API max, found {len(job_urls)})")
        job_urls = job_urls[:50]
    
    # Step 3: Extract content with Parallel
    extract_data = await parallel_extract(parallel_key, job_urls)
    if not extract_data:
        print("\n❌ Extraction failed. Aborting.")
        return
    
    # Structure and export
    jobs = structure_jobs(extract_data)
    if jobs:
        csv_path = export_csv(jobs)
        
        print("\n" + "="*80)
        print(f"✅ TEST COMPLETE!")
        print(f"📊 Found {len(jobs)} Indeed jobs for {CITY}")
        print(f"📁 Results saved in: {RESULTS_DIR}")
        print("="*80)
    else:
        print("\n❌ No structured jobs created.")

if __name__ == "__main__":
    asyncio.run(main())
