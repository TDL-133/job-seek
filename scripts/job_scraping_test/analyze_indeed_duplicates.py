#!/usr/bin/env python3
"""
Analyze Indeed URLs to identify duplication patterns.
"""
import asyncio
import re
from collections import Counter
from parallel_scraper import ParallelScraper
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / ".env")

async def analyze_indeed_duplicates():
    """Analyze Indeed URL patterns to find duplicates"""
    
    # Initialize scraper
    parallel_api_key = os.getenv("PARALLEL_API_KEY")
    scraper = ParallelScraper(parallel_api_key)
    
    # Run Phase 1
    job_title = "Customer Success Manager"
    city = "Marseille"
    region = "Provence-Alpes-Côte d'Azur"
    limit_per_source = 10
    
    urls, _ = await scraper.phase1_search(job_title, city, region, limit_per_source)
    
    # Filter Indeed URLs
    indeed_urls = [u for u in urls if 'indeed.com' in u]
    
    print(f"\n📊 INDEED URL ANALYSIS ({len(indeed_urls)} URLs)")
    print("=" * 70)
    
    # Extract job IDs
    job_ids = []
    patterns = {
        'viewjob': re.compile(r'/viewjob\?jk=([a-f0-9]+)'),
        'rc_clk': re.compile(r'/rc/clk\?jk=([a-f0-9]+)'),
        'cmp_jobs': re.compile(r'/cmp/[^/]+/jobs/([^?]+)')
    }
    
    for url in indeed_urls:
        for pattern_name, pattern in patterns.items():
            match = pattern.search(url)
            if match:
                job_id = match.group(1)
                job_ids.append((job_id, pattern_name, url))
                break
    
    # Count duplicate job IDs
    id_counts = Counter([jid for jid, _, _ in job_ids])
    duplicates = {jid: count for jid, count in id_counts.items() if count > 1}
    
    print(f"\nTotal Indeed URLs: {len(indeed_urls)}")
    print(f"Unique job IDs: {len(id_counts)}")
    print(f"Duplicate job IDs: {len(duplicates)}")
    print(f"Expected jobs (manual): 16")
    print(f"\n⚠️ Excess URLs: {len(indeed_urls) - 16}")
    
    # Show top duplicates
    if duplicates:
        print(f"\n🔍 TOP 10 DUPLICATES:")
        for i, (jid, count) in enumerate(sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10], 1):
            print(f"\n   {i}. Job ID '{jid}' appears {count} times:")
            matching_urls = [url for id, _, url in job_ids if id == jid]
            for url in matching_urls[:3]:  # Show first 3
                print(f"      - {url[:80]}...")
    
    # Show URL pattern distribution
    print(f"\n📈 URL PATTERN DISTRIBUTION:")
    pattern_counts = Counter([pname for _, pname, _ in job_ids])
    for pattern, count in pattern_counts.items():
        print(f"   {pattern}: {count} URLs")
    
    # Sample of first 10 URLs
    print(f"\n📋 SAMPLE - First 10 Indeed URLs:")
    for i, url in enumerate(indeed_urls[:10], 1):
        # Extract job ID for this URL
        jid = None
        for job_id, _, u in job_ids:
            if u == url:
                jid = job_id
                break
        dup_marker = " ⚠️ DUPLICATE" if jid and id_counts.get(jid, 0) > 1 else ""
        print(f"   {i}. {url[:75]}...{dup_marker}")

if __name__ == "__main__":
    asyncio.run(analyze_indeed_duplicates())
