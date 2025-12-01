#!/usr/bin/env python3
"""
Test script to analyze Phase 1 filtering logic.
Loads existing search results and re-applies filtering to understand the imbalance.
"""
import json
from pathlib import Path

results_dir = Path("results")

# Load search results
with open(results_dir / "parallel_search.json") as f:
    parallel = json.load(f)
with open(results_dir / "tavily_search.json") as f:
    tavily = json.load(f)
with open(results_dir / "firecrawl_indeed.json") as f:
    firecrawl = json.load(f)

# Extract URLs
parallel_urls = [r["url"] for r in parallel.get("results", [])]
tavily_urls = [r["url"] for r in tavily.get("results", [])]
indeed_urls = firecrawl.get("job_urls", [])

print("=" * 80)
print("PHASE 1 RAW RESULTS ANALYSIS")
print("=" * 80)

# Analyze by source
def analyze_urls(urls, source_name):
    glassdoor = [u for u in urls if 'glassdoor.com' in u.lower()]
    wttj = [u for u in urls if 'welcometothejungle.com' in u.lower()]
    indeed = [u for u in urls if 'indeed.com' in u.lower()]
    
    print(f"\n{source_name}:")
    print(f"  Total: {len(urls)}")
    print(f"  Glassdoor: {len(glassdoor)}")
    print(f"  WTTJ: {len(wttj)}")
    print(f"  Indeed: {len(indeed)}")
    
    # Show Glassdoor patterns
    if glassdoor:
        print(f"\n  Glassdoor URLs:")
        for url in glassdoor[:5]:
            print(f"    - {url}")
    
    # Show WTTJ patterns
    if wttj:
        print(f"\n  WTTJ URLs:")
        for url in wttj[:5]:
            print(f"    - {url}")

analyze_urls(parallel_urls, "PARALLEL SEARCH")
analyze_urls(tavily_urls, "TAVILY SEARCH")
analyze_urls(indeed_urls, "FIRECRAWL INDEED")

# Combined analysis
all_urls = parallel_urls + tavily_urls + indeed_urls
unique_urls = list(set(all_urls))

print(f"\n{'=' * 80}")
print("COMBINED ANALYSIS")
print(f"{'=' * 80}")
print(f"Total raw URLs: {len(all_urls)}")
print(f"Unique URLs: {len(unique_urls)}")

glassdoor_urls = [u for u in unique_urls if 'glassdoor.com' in u.lower()]
wttj_urls = [u for u in unique_urls if 'welcometothejungle.com' in u.lower()]
indeed_urls_unique = [u for u in unique_urls if 'indeed.com' in u.lower()]

print(f"\nGlassdoor: {len(glassdoor_urls)} unique URLs")
print(f"WTTJ: {len(wttj_urls)} unique URLs")
print(f"Indeed: {len(indeed_urls_unique)} unique URLs")

# Analyze Glassdoor patterns
print(f"\n{'=' * 80}")
print("GLASSDOOR URL PATTERNS")
print(f"{'=' * 80}")
for url in glassdoor_urls:
    if 'SRCH_IL' in url or 'SRCH_IC' in url:
        print(f"✅ LISTING PAGE: {url[:100]}")
    elif '/job-listing/' in url or '/partner/' in url:
        print(f"✅ JOB POST: {url[:100]}")
    elif '/Salaries/' in url or '/Salary/' in url:
        print(f"❌ SALARY PAGE: {url[:100]}")
    else:
        print(f"⚠️  UNKNOWN: {url[:100]}")

# Analyze WTTJ patterns
print(f"\n{'=' * 80}")
print("WTTJ URL PATTERNS")
print(f"{'=' * 80}")
for url in wttj_urls:
    if '/companies/' in url and '/jobs/' in url:
        print(f"✅ JOB POST: {url[:100]}")
    elif '/pages/' in url:
        print(f"❌ LANDING PAGE: {url[:100]}")
    else:
        print(f"⚠️  UNKNOWN: {url[:100]}")

print(f"\n{'=' * 80}")
print("RECOMMENDATION")
print(f"{'=' * 80}")
print("""
1. GLASSDOOR: 7 listing pages found → Need to SCRAPE each to extract ~10 individual jobs
2. WTTJ: Mostly landing pages → Need better search strategy or direct company job pages
3. INDEED: 130 URLs → Need deduplication + validation that jobs match query
""")
