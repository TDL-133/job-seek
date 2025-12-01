#!/usr/bin/env python3
"""
Test Unipile LinkedIn search for Product Manager jobs in Lyon.

This script tests ONLY LinkedIn via Unipile API:
1. Unipile Search → Get LinkedIn job listings
2. Extract structured data
3. Filter by Lyon location
4. Export to CSV
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

async def unipile_search_linkedin():
    """Search LinkedIn jobs using Unipile API."""
    unipile_dsn = os.getenv("UNIPILE_DSN")
    unipile_api_key = os.getenv("UNIPILE_API_KEY")
    unipile_account_id = os.getenv("UNIPILE_LINKEDIN_ACCOUNT_ID")
    
    if not all([unipile_dsn, unipile_api_key, unipile_account_id]):
        print("❌ Missing Unipile credentials in .env")
        return None
    
    print(f"\n🔗 UNIPILE LINKEDIN SEARCH")
    print(f"   Query: {JOB_TITLE} in {CITY}")
    print(f"   Account: ...{unipile_account_id[-5:]}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{unipile_dsn}/api/v1/linkedin/search",
                headers={
                    "X-API-KEY": unipile_api_key,
                    "accept": "application/json",
                    "content-type": "application/json"
                },
                params={"account_id": unipile_account_id},
                json={
                    "api": "classic",
                    "category": "jobs",
                    "keywords": f'"{JOB_TITLE}" AND "{CITY}"',
                    "limit": 30,
                    "count": 30
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Save raw response
                with open(RESULTS_DIR / "unipile_linkedin_raw.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                print(f"   ✅ API Response: {response.status_code}")
                print(f"   📊 Total items returned: {len(data.get('items', []))}")
                
                return data
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
                return None
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def parse_and_filter_jobs(data):
    """Parse Unipile response and filter for Lyon jobs."""
    print(f"\n📊 PARSING & FILTERING")
    
    items = data.get("items", [])
    jobs = []
    skipped = 0
    
    for item in items:
        # Only process JOB type items
        if item.get("type") != "JOB":
            continue
        
        # Extract fields
        title = item.get("title", "Unknown Title")
        location = item.get("location", "")
        
        company_data = item.get("company", {})
        if isinstance(company_data, dict):
            company = company_data.get("name", "Unknown Company")
        else:
            company = str(company_data)
        
        # Extract URL
        url = item.get("job_url") or item.get("url") or item.get("link")
        if not url:
            continue
        
        # FILTER: Only keep Lyon jobs
        if location:
            location_lower = location.lower()
            if CITY.lower() not in location_lower:
                skipped += 1
                print(f"   ⊗ Skipped: {title[:50]} in {location}")
                continue
        else:
            # No location - skip to be safe
            skipped += 1
            print(f"   ⊗ Skipped: {title[:50]} (no location)")
            continue
        
        # Extract additional fields
        description = item.get("description", "")
        posted_date = item.get("posted_date", "Not specified")
        
        job = {
            "title": title,
            "company": company,
            "location": location,
            "salary": "Not specified",
            "contract_type": "CDI" if "cdi" in description.lower() else "Not specified",
            "remote": "Hybrid" if "hybrid" in description.lower() or "télétravail" in description.lower() else "Not specified",
            "description": description[:200] + "..." if len(description) > 200 else description,
            "skills": "",
            "posted_date": posted_date,
            "url": url,
            "source": "linkedin",
            "extraction_method": "unipile"
        }
        
        jobs.append(job)
        print(f"   ✅ {title[:50]} @ {location}")
    
    print(f"\n   📊 Kept {len(jobs)} jobs matching {CITY}")
    print(f"   ⊗ Filtered out {skipped} jobs (wrong/no location)")
    
    return jobs

def export_csv(jobs):
    """Export jobs to CSV."""
    csv_path = RESULTS_DIR / "linkedin_jobs.csv"
    
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
    
    # Also save JSON
    with open(RESULTS_DIR / "linkedin_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    return csv_path

async def main():
    print("="*80)
    print("🔗 TEST: Unipile LinkedIn Search")
    print(f"🎯 Search: {JOB_TITLE} in {CITY}, {REGION}")
    print("="*80)
    
    # Search LinkedIn via Unipile
    data = await unipile_search_linkedin()
    if not data:
        print("\n❌ Search failed. Aborting.")
        return
    
    # Parse and filter
    jobs = parse_and_filter_jobs(data)
    if not jobs:
        print("\n❌ No jobs found matching Lyon.")
        return
    
    # Export
    csv_path = export_csv(jobs)
    
    print("\n" + "="*80)
    print(f"✅ TEST COMPLETE!")
    print(f"📊 Found {len(jobs)} LinkedIn jobs for {CITY}")
    print(f"📁 Results saved in: {RESULTS_DIR}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
