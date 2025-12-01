#!/usr/bin/env python3
"""
Test ONLY Phase 1 filtering to validate URL collection and filtering logic.

Usage:
    python test_phase1_only.py "Job Title" "City" "Region" [limit]
    
Examples:
    python test_phase1_only.py "Product Designer" "Lille" "Hauts-de-France"
    python test_phase1_only.py "Customer Success Manager" "Marseille" "Provence-Alpes-Côte d'Azur" 10
"""
import asyncio
import sys
from parallel_scraper import ParallelScraper
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def test_phase1_only():
    """Run only Phase 1: Multi-Source Search and Filtering"""
    
    # Parameters from command line or defaults
    if len(sys.argv) >= 4:
        job_title = sys.argv[1]
        city = sys.argv[2]
        region = sys.argv[3]
        limit_per_source = int(sys.argv[4]) if len(sys.argv) >= 5 else 10
    else:
        # Default parameters
        print("⚠️  No arguments provided. Using defaults.")
        print("Usage: python test_phase1_only.py \"Job Title\" \"City\" \"Region\" [limit]\n")
        job_title = "Customer Success Manager"
        city = "Marseille"
        region = "Provence-Alpes-Côte d'Azur"
        limit_per_source = 10
    
    print("=" * 70)
    print("PHASE 1 ONLY TEST - URL COLLECTION & FILTERING")
    print("=" * 70)
    print(f"\n🚀 Query: '{job_title}' in '{city}, {region}'")
    print(f"📍 Target: {city} ({region})")
    print(f"📍 Limit: {limit_per_source} jobs per source (Glassdoor + WTTJ + Indeed + LinkedIn)")
    print("=" * 70)
    
    # Initialize scraper
    parallel_api_key = os.getenv("PARALLEL_API_KEY")
    if not parallel_api_key:
        print("❌ PARALLEL_API_KEY not found in .env")
        sys.exit(1)
    
    scraper = ParallelScraper(parallel_api_key)
    
    # Run Phase 1 only
    print("\n📡 PHASE 1: Multi-Source Search")
    urls, linkedin_job_objects = await scraper.phase1_search(job_title, city, region, limit_per_source)
    
    # Detailed breakdown by source
    glassdoor_urls = [u for u in urls if 'glassdoor' in u]
    wttj_urls = [u for u in urls if 'welcometothejungle' in u]
    indeed_urls = [u for u in urls if 'indeed' in u]
    linkedin_urls = [u for u in urls if 'linkedin' in u]
    
    print("\n" + "=" * 70)
    print("PHASE 1 RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n✅ Found {len(urls)} URLs for scraping + {len(linkedin_job_objects)} LinkedIn jobs (direct):")
    print(f"   - Glassdoor: {len(glassdoor_urls)}")
    print(f"   - WTTJ: {len(wttj_urls)}")
    print(f"   - Indeed: {len(indeed_urls)}")
    print(f"   - LinkedIn: {len(linkedin_job_objects)} (via Unipile)")
    
    # Show Glassdoor URLs
    if glassdoor_urls:
        print(f"\n📊 GLASSDOOR URLS ({len(glassdoor_urls)}):")
        listing_pages = [u for u in glassdoor_urls if 'SRCH_IL' in u or 'SRCH_IC' in u]
        job_pages = [u for u in glassdoor_urls if u not in listing_pages]
        
        if listing_pages:
            print(f"   ⚠️ STILL HAVE {len(listing_pages)} LISTING PAGES (Expansion failed?):")
            for i, url in enumerate(listing_pages, 1):
                print(f"   {i}. 🔍 {url[:90]}...")
        
        if job_pages:
            print(f"   ✅ Have {len(job_pages)} individual job pages:")
            for i, url in enumerate(job_pages[:5], 1):
                print(f"   {i}. ✓ {url[:90]}...")
            if len(job_pages) > 5:
                print(f"   ... and {len(job_pages)-5} more")
    
    # Show WTTJ URLs (should be 1 valid job)
    if wttj_urls:
        print(f"\n📊 WTTJ URLS ({len(wttj_urls)}):")
        for i, url in enumerate(wttj_urls, 1):
            if '/companies/' in url and '/jobs/' in url:
                print(f"   {i}. ✅ VALID JOB: {url[:90]}...")
            else:
                print(f"   {i}. ⚠️ UNKNOWN: {url[:90]}...")
    
    # Show Indeed summary (130 URLs is too many to display all)
    if indeed_urls:
        print(f"\n📊 INDEED URLS ({len(indeed_urls)}):")
        print(f"   Total: {len(indeed_urls)} URLs")
        print(f"   Expected from manual search: 16 jobs")
        print(f"   ⚠️ ISSUE: {len(indeed_urls) - 16} extra URLs (likely duplicates)")
        # Show first 3 and last 3
        print(f"\n   First 3:")
        for i, url in enumerate(indeed_urls[:3], 1):
            print(f"   {i}. {url[:90]}...")
        print(f"\n   Last 3:")
        for i, url in enumerate(indeed_urls[-3:], len(indeed_urls)-2):
            print(f"   {i}. {url[:90]}...")
    
    # Show LinkedIn summary
    if linkedin_job_objects:
        print(f"\n📊 LINKEDIN JOBS ({len(linkedin_job_objects)}) via Unipile:")
        for i, job in enumerate(linkedin_job_objects, 1):
            title = job.get('title', 'Unknown')
            company = job.get('company', {})
            company_name = company.get('name', 'Unknown') if isinstance(company, dict) else str(company)
            print(f"   {i}. {title} @ {company_name}")

    # EXPORT URLS TO FILE
    with open("phase1_urls.md", "w") as f:
        f.write(f"# Phase 1 Results URLs ({len(urls) + len(linkedin_job_objects)} total)\n\n")
        
        f.write(f"## WTTJ ({len(wttj_urls)})\n")
        for u in wttj_urls: f.write(f"- {u}\n")
        
        f.write(f"\n## LinkedIn ({len(linkedin_job_objects)})\n")
        for job in linkedin_job_objects:
             u = job.get("job_url") or job.get("url") or job.get("link") or "No URL"
             title = job.get('title', 'Unknown')
             company = job.get('company', {}).get('name', 'Unknown')
             f.write(f"- {u} ({title} @ {company})\n")

        f.write(f"\n## Glassdoor ({len(glassdoor_urls)})\n")
        for u in glassdoor_urls: f.write(f"- {u}\n")

        f.write(f"\n## Indeed ({len(indeed_urls)})\n")
        for u in indeed_urls: f.write(f"- {u}\n")
    
    print(f"\n✅ URLs exported to phase1_urls.md")

    # Expected vs Actual
    print("\n" + "=" * 70)
    print("EXPECTED VS ACTUAL COMPARISON")
    print("=" * 70)
    print(f"\nGlassdoor:")
    print(f"  Manual search: 27 jobs")
    print(f"  Script found:  {len(glassdoor_urls)} jobs (extracted from listing pages)")
    
    print(f"\nWTTJ:")
    print(f"  Manual search: 15 jobs")
    print(f"  Script found:  {len(wttj_urls)} job(s)")
    
    print(f"\nIndeed:")
    print(f"  Manual search: 16 jobs")
    print(f"  Script found:  {len(indeed_urls)} URLs")
    
    print(f"\nLinkedIn:")
    print(f"  Script found:  {len(linkedin_job_objects)} jobs (via Unipile)")
    
    # Issues summary
    print("\n" + "=" * 70)
    print("ISSUES IDENTIFIED")
    print("=" * 70)
    
    if len(glassdoor_urls) >= 15:
        print("\n✅ Glassdoor: Expansion successful (found >= 15 jobs)")
    elif len(glassdoor_urls) > 0:
        print(f"\n⚠️ Glassdoor: Found {len(glassdoor_urls)} jobs (expected ~27). Check expansion.")
    else:
        print("\n❌ Glassdoor: No jobs found")
    
    if len(wttj_urls) >= 5:
        print(f"\n✅ WTTJ: Found {len(wttj_urls)} jobs (Improvement!)")
    elif len(wttj_urls) > 0:
        print(f"\n⚠️ WTTJ: Found {len(wttj_urls)} jobs (Still low vs 15 expected)")
    else:
        print("\n❌ WTTJ: No jobs found")
    
    if len(indeed_urls) == 130:
        print("\n⚠️ Indeed: 130 URLs found vs 16 expected")
        print("   ACTION NEEDED: Deduplicate and validate URLs")
    
    if len(linkedin_job_objects) == 4:
        print("\n✅ LinkedIn: 4 jobs via Unipile (WORKING)")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE - Phase 1 filtering analysis done")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_phase1_only())
