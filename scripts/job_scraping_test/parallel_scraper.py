#!/usr/bin/env python3
"""
Multi-source Job Scraper combining Parallel.ai and Firecrawl.

This script searches for job postings using a hybrid approach:
1. Phase 1: Search with Parallel Search API + Firecrawl Search MCP
2. Phase 2: Extract content with Parallel Extract API
3. Phase 3: Structure and export to CSV

Author: Job Seek Team
Date: 2024-11-28
"""
import asyncio
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote
import httpx
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class ParallelScraper:
    """Multi-source job scraper using Parallel.ai and Firecrawl APIs."""
    
    def __init__(self, api_key: str):
        """
        Initialize the scraper.
        
        Args:
            api_key: Parallel.ai API key
        """
        self.api_key = api_key
        self.parallel_base_url = "https://api.parallel.ai/v1beta"
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.headers = {
            "x-api-key": self.api_key,
            "parallel-beta": "search-extract-2025-10-10",
            "Content-Type": "application/json"
        }
        
    async def run(self, job_title: str, city: str, region: str, limit_per_source: int = 3):
        """
        Main orchestrator for the scraping workflow.
        
        Args:
            job_title: Job title to search (e.g., "Product Manager")
            city: City to search (e.g., "Lyon")
            region: Region to search (e.g., "Auvergne-Rhône-Alpes")
            limit_per_source: Max jobs per platform
            
        Returns:
            Path to generated CSV file
        """
        print(f"\n🚀 Starting job search: '{job_title}' in '{city}, {region}'")
        print(f"📍 Target: {city} ({region})")
        print(f"📍 Limit: {limit_per_source} jobs per source (Glassdoor + WTTJ + Indeed + LinkedIn)")
        print("=" * 70)
        
        # Phase 1: Search
        print("\n📡 PHASE 1: Multi-Source Search")
        urls, linkedin_job_objects = await self.phase1_search(job_title, city, region, limit_per_source)
        
        if not urls and not linkedin_job_objects:
            print("❌ No job URLs found. Exiting.")
            return None
        
        print(f"\n✅ Found {len(urls)} URLs for scraping + {len(linkedin_job_objects)} LinkedIn jobs (direct):")
        glassdoor_count = len([u for u in urls if 'glassdoor.com' in u])
        wttj_count = len([u for u in urls if 'welcometothejungle.com' in u])
        indeed_count = len([u for u in urls if 'indeed.com' in u])
        print(f"   - Glassdoor: {glassdoor_count}")
        print(f"   - WTTJ: {wttj_count}")
        print(f"   - Indeed: {indeed_count}")
        print(f"   - LinkedIn: {len(linkedin_job_objects)} (via Unipile)")
        
        # Phase 2: Extract (skipping LinkedIn - handled directly from Unipile)
        print("\n🔍 PHASE 2: Content Extraction")
        if urls:
            extract_results = await self.phase2_extract(urls)
            if not extract_results:
                print("⚠️ Extraction failed for some URLs. Continuing with LinkedIn jobs...")
                extract_results = {"results": []}
        else:
            print("   ⚡ No URLs to scrape (LinkedIn-only search)")
            extract_results = {"results": []}
        
        # Parse LinkedIn jobs from Unipile
        print("\n🔗 PHASE 2.5: Parsing LinkedIn Jobs from Unipile")
        linkedin_structured_jobs = self._parse_unipile_jobs(linkedin_job_objects) if linkedin_job_objects else []
        print(f"   ✓ Parsed {len(linkedin_structured_jobs)} LinkedIn jobs")
        
        # Phase 3: Structure and export
        print("\n📊 PHASE 3: Data Structuring & Export")
        structured_jobs = self.phase3_structure(extract_results, linkedin_structured_jobs)
        
        if not structured_jobs:
            print("❌ No structured jobs. Exiting.")
            return None
        
        # Phase 3.5: Geographic filtering (post-extraction)
        print("\n🗺️ PHASE 3.5: Geographic Filtering")
        filtered_jobs = self._filter_by_location(structured_jobs, city)
        
        if not filtered_jobs:
            print("❌ No jobs match the specified location. Exiting.")
            return None
        
        print(f"   ✓ Kept {len(filtered_jobs)}/{len(structured_jobs)} jobs matching '{city}'")
        
        # Save filtered jobs to JSON (overwrite previous)
        with open(self.results_dir / "jobs.json", "w") as f:
            json.dump(filtered_jobs, f, indent=2, ensure_ascii=False)
        
        csv_path = self.export_csv(filtered_jobs)
        
        print("\n" + "=" * 70)
        print(f"✅ SUCCESS! Found {len(structured_jobs)} complete job postings")
        print(f"📄 CSV: {csv_path}")
        print(f"📁 JSON files saved in: {self.results_dir}")
        
        return csv_path
    
    def _filter_job_urls(self, urls: List[str]) -> List[str]:
        """
        Filter out non-job-specific URLs.
        
        Excludes aggregated pages, salary pages, company overviews, etc.
        Only keeps URLs that point to individual job postings.
        
        Also deduplicates Indeed URLs by job ID (to avoid /viewjob, /rc/clk variants).
        """
        excluded_patterns = [
            # Glassdoor exclusions
            '/Salaries/',
            '/Overview/',
            '/Reviews/',
            '/Interview/',
            '/Location/',
            # Generic exclusions
            '/search',
            '/categories',
        ]
        
        # Track Indeed job IDs to deduplicate
        indeed_job_ids = set()
        
        filtered = []
        for url in urls:
            # Skip if contains excluded patterns
            if any(pattern in url for pattern in excluded_patterns):
                print(f"   ⊗ Filtered out: {url[:80]}...")
                continue
            
            # WTTJ: Must have /jobs/ in path AND must be a specific job (not landing page)
            if 'welcometothejungle.com' in url:
                # Accept ONLY specific job postings with format: /companies/{company}/jobs/{job-slug}_{location}
                if '/companies/' in url and '/jobs/' in url and url.count('/') >= 6:
                    filtered.append(url)
                    print(f"   ✓ Accepted WTTJ job: {url[:80]}...")
                # Reject landing pages, category pages, homepages
                elif '/pages/' in url or url.endswith('/en') or url.endswith('/fr') or url.endswith('/es'):
                    print(f"   ⊗ Filtered out (WTTJ landing/home page): {url[:80]}...")
                else:
                    print(f"   ⊗ Filtered out (WTTJ non-job): {url[:80]}...")
            
            # Glassdoor: Accept individual postings AND location-specific search pages
            elif 'glassdoor.com' in url:
                # Accept individual job postings
                if '/job-listing/' in url or '/partner/' in url:
                    filtered.append(url)
                    print(f"   ✓ Accepted Glassdoor job posting: {url[:80]}...")
                # Accept location-specific search pages (contain job listings)
                elif '/Job/' in url and ('SRCH_IL' in url or 'SRCH_IC' in url):
                    filtered.append(url)
                    print(f"   🔍 Accepted Glassdoor listing page: {url[:80]}...")
                # Reject generic/global search pages
                elif '/Job/' in url and 'SRCH_IN' in url:
                    print(f"   ⊗ Filtered out (Glassdoor global search): {url[:80]}...")
                # Reject other non-job pages
                else:
                    print(f"   ⊗ Filtered out (Glassdoor non-job): {url[:80]}...")
            
            # Indeed: Accept job postings (with deduplication by job ID)
            elif 'indeed.com' in url:
                # Extract job ID for deduplication
                job_id = None
                
                # Try to extract job ID from URL
                if '/viewjob?jk=' in url or '/rc/clk?jk=' in url:
                    match = re.search(r'jk=([a-f0-9]+)', url)
                    if match:
                        job_id = match.group(1)
                elif '/cmp/' in url and '/jobs/' in url:
                    match = re.search(r'/jobs/([^?]+)', url)
                    if match:
                        job_id = match.group(1)
                
                # Check for duplicates
                if job_id and job_id in indeed_job_ids:
                    print(f"   ⊗ Filtered out (Indeed duplicate job_id={job_id}): {url[:60]}...")
                    continue
                
                # Accept individual job postings
                if '/viewjob?jk=' in url or '/rc/clk?jk=' in url:
                    if job_id:
                        indeed_job_ids.add(job_id)
                    filtered.append(url)
                # Accept company-hosted jobs
                elif '/cmp/' in url and '/jobs/' in url:
                    if job_id:
                        indeed_job_ids.add(job_id)
                    filtered.append(url)
                # Reject search result pages (pattern: /q-...-emplois.html or /jobs?q=)
                elif '/q-' in url and '-emplois.html' in url:
                    print(f"   ⊗ Filtered out (Indeed search results page): {url[:80]}...")
                # Reject other non-job pages
                elif '/jobs?q=' in url or '/companies/' in url or '/career-advice/' in url or '/salaries/' in url:
                    print(f"   ⊗ Filtered out (Indeed non-job): {url[:80]}...")
                else:
                    # Accept other Indeed URLs by default (to be permissive)
                    if job_id:
                        indeed_job_ids.add(job_id)
                    filtered.append(url)
                    print(f"   ⚠️  Accepted Indeed URL (unknown pattern): {url[:80]}...")
            
            # LinkedIn: Accept job postings (from Unipile, most are valid)
            elif 'linkedin.com' in url:
                # Accept individual job postings only
                if '/jobs/view/' in url:
                    filtered.append(url)
                # Reject search result pages with patterns like:
                # - /jobs/product-owner-jobs-lyon
                # - /jobs/head-of-product-jobs-lyon
                # - /jobs/search/
                elif '/jobs/search/' in url or '/company/' in url or '-jobs-' in url:
                    print(f"   ⊗ Filtered out (LinkedIn search/aggregation page): {url[:80]}...")
                else:
                    # Accept other LinkedIn job URLs by default (but warn)
                    filtered.append(url)
                    print(f"   ⚠️  Accepted LinkedIn URL (unknown pattern): {url[:80]}...")
            
            # Other domains
            else:
                filtered.append(url)
        
        return filtered
    
    def _filter_by_location(self, jobs: List[Dict], target_location: str) -> List[Dict]:
        """
        Filter jobs by location after extraction.
        
        This is a post-extraction filter that checks if the parsed location field
        contains the target location. This catches jobs that passed URL filtering
        but are actually in a different city.
        
        Args:
            jobs: List of structured job dicts
            target_location: Target location (e.g., "Toulouse")
            
        Returns:
            List of jobs matching the target location
        """
        filtered_jobs = []
        target_lower = target_location.lower()
        
        for job in jobs:
            location = job.get("location", "").lower()
            
            # Skip if location is unknown/unparsed
            if not location or location in ["unknown location", "input box label"]:
                # Keep job but log warning
                filtered_jobs.append(job)
                print(f"   ⚠️  Kept job with unparsed location: {job['title'][:40]}... ({job['source']})")
                continue
            
            # Check if target location is in the parsed location
            if target_lower in location:
                filtered_jobs.append(job)
                print(f"   ✅ {job['source'].upper()}: {job['title'][:40]}... in {location}")
            else:
                print(f"   ⊗ Filtered {job['source'].upper()}: {job['title'][:40]}... (location: {location}, expected: {target_location})")
        
        return filtered_jobs
    
    async def _tavily_search_api(self, job_title: str, city: str, region: str, max_results: int) -> List[str]:
        """
        Search for job URLs using Tavily API (REST).
        
        Requires TAVILY_API_KEY environment variable.
        Falls back gracefully if not available.
        """
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            print(f"   ⚠️  TAVILY_API_KEY not set, skipping Tavily search")
            # Save placeholder
            with open(self.results_dir / "tavily_search.json", "w") as f:
                json.dump({
                    "note": "TAVILY_API_KEY not configured",
                    "hint": "Set TAVILY_API_KEY in .env to enable Tavily search (free tier: 1000 searches/month at https://tavily.com/)"
                }, f, indent=2)
            return []
        
        try:
            # Tavily API has a strict limit of 20 results per request
            # We must cap it to avoid 400 Bad Request, even if user requested more
            effective_limit = min(max_results, 20)
            
            query = f"{job_title} job {city} {region} site:fr.indeed.com"
            print(f"   🔎 Tavily API query: {query} (requesting up to {effective_limit} results - Tavily API limit)")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": effective_limit,
                        "include_domains": ["fr.indeed.com"]
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    urls = [r["url"] for r in data.get("results", [])]
                    
                    # Save results
                    with open(self.results_dir / "tavily_search.json", "w") as f:
                        json.dump(data, f, indent=2)
                    
                    return urls
                else:
                    print(f"   ⚠️  Tavily API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"   ⚠️  Tavily error: {type(e).__name__}: {e}")
            return []
    
    def _match_job_title(self, query_title: str, scraped_title: str, min_terms: int = 2) -> bool:
        """
        Check if scraped job title matches the query title.
        
        Args:
            query_title: The search query (e.g., "Customer Success Manager")
            scraped_title: Job title from scraped page (e.g., "Customer Success Specialist F/H")
            min_terms: Minimum number of matching terms required (default: 2)
            
        Returns:
            True if at least min_terms match between query and scraped title
        """
        # Strip underscores from Firecrawl search highlights (e.g., _Customer_ -> Customer)
        scraped_title = scraped_title.replace('_', '')
        
        # Extract key terms (lowercase, filter out short words and common terms)
        stop_words = {'h', 'f', 'hf', 'fn', 'mfd', 'cdi', 'stage', 'alternance', 'de', 'le', 'la', 'et', 'ou', 'in', 'at', 'the', 'a', 'an'}
        
        query_terms = set()
        for term in query_title.lower().split():
            if len(term) > 2 and term not in stop_words:
                query_terms.add(term)
        
        scraped_terms = set()
        for term in scraped_title.lower().split():
            if len(term) > 2 and term not in stop_words:
                scraped_terms.add(term)
        
        # Count matches
        matches = query_terms & scraped_terms
        return len(matches) >= min_terms
    
    async def _firecrawl_search_indeed(self, job_title: str, city: str, region: str, max_results: int) -> List[str]:
        """
        Search Indeed using Firecrawl Scrape on the direct search results page.
        Optimized for France (.fr) as per user requirements.
        """
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        if not firecrawl_api_key:
            return []
            
        # Construct URL
        # Example: https://fr.indeed.com/jobs?q=Customer%20Success%20Manager&l=Marseille
        query_encoded = quote(job_title)
        loc_encoded = quote(city)
        url = f"https://fr.indeed.com/jobs?q={query_encoded}&l={loc_encoded}"
        
        print(f"   🔥 Firecrawl Indeed Search: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {firecrawl_api_key}",
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
                    
                    # Extract job links
                    # Indeed Patterns: /viewjob?jk=..., /rc/clk?jk=..., /company/.../jobs/...
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
                            
                    print(f"   ✓ Found {len(urls)} Indeed jobs via Firecrawl")
                    return urls
                else:
                    print(f"   ⚠️ Firecrawl Indeed error: {response.status_code}")
                    return []
        except Exception as e:
            print(f"   ⚠️ Firecrawl Indeed exception: {e}")
            return []
    
    async def _firecrawl_search_wttj(self, job_title: str, city: str, region: str, max_results: int) -> List[str]:
        """
        Search WTTJ using Firecrawl Scrape on the search results page.
        Filters results by job title match to exclude unrelated jobs.
        """
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        if not firecrawl_api_key:
            return []
            
        # Construct URL
        # Example: https://www.welcometothejungle.com/fr/jobs?query=Customer%20Success%20Manager&aroundQuery=Marseille
        query_encoded = quote(job_title)
        loc_encoded = quote(city)
        url = f"https://www.welcometothejungle.com/fr/jobs?query={query_encoded}&aroundQuery={loc_encoded}"
        
        print(f"   🔥 Firecrawl WTTJ Search: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {firecrawl_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "formats": ["html", "markdown"],
                        "onlyMainContent": False,
                        "waitFor": 5000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    html = data.get("data", {}).get("html", "")
                    markdown = data.get("data", {}).get("markdown", "")
                    
                    # Extract links: /companies/{company}/jobs/{slug}
                    url_matches = re.findall(r'href=["\']([^"\']*/companies/[^"\'/]+/jobs/[^"\']*)["\']', html)
                    
                    # Extract job titles from markdown (pattern: **Title**)
                    # Job titles appear as bold text in job cards
                    title_matches = re.findall(r'\*\*([^*]+)\*\*', markdown)
                    
                    # Build URL set
                    all_urls = set()
                    for match in url_matches:
                        if match.startswith('/'):
                            match = f"https://www.welcometothejungle.com{match}"
                        all_urls.add(match)
                    
                    print(f"   ✓ Found {len(all_urls)} WTTJ jobs before filtering")
                    
                    # Extract locations from markdown
                    # Locations appear as city names in job cards (e.g., "Paris", "Marseille", "Marseille, Lyon")
                    # Simple pattern: capital letter followed by lowercase, possibly comma-separated
                    location_pattern = r'\n([A-Z][a-zéèê\-]+(?:,\s*[A-Z][a-zéèê\-]+)*)\n'
                    location_matches = re.findall(location_pattern, markdown)
                    
                    # Filter locations to actual city names (exclude company names, job types, etc.)
                    # Common French cities we want to match
                    known_cities = {
                        'paris', 'marseille', 'lyon', 'toulouse', 'nice', 'nantes', 'strasbourg',
                        'montpellier', 'bordeaux', 'lille', 'rennes', 'reims', 'toulon', 'grenoble',
                        'dijon', 'angers', 'nîmes', 'villeurbanne', 'clermont', 'aix', 'brest',
                        'tours', 'amiens', 'limoges', 'annecy', 'perpignan', 'metz', 'besançon',
                        'orleans', 'mulhouse', 'rouen', 'caen', 'nancy', 'argenteuil', 'saint',
                        'montreuil', 'roubaix', 'tourcoing', 'avignon', 'poitiers', 'versailles',
                        'courbevoie', 'vitry', 'créteil', 'pau', 'la', 'cannes', 'antibes',
                        'puteaux', 'boulogne', 'rambouillet', 'aubagne', 'salon'
                    }
                    
                    city_locations = []
                    for loc in location_matches:
                        # Check if it's a city (at least one word matches known cities)
                        loc_words = loc.lower().replace(',', ' ').split()
                        if any(word in known_cities for word in loc_words):
                            city_locations.append(loc)
                    
                    # Normalize target city for matching
                    target_city_lower = city.lower()
                    
                    # Build URL-to-location mapping using HTML proximity
                    # We'll check if location appears near URL in HTML
                    url_to_location = {}
                    for url in all_urls:
                        # Find URL position in HTML
                        url_escaped = url.replace('/', '\\/')
                        url_pos = html.find(url)
                        if url_pos == -1:
                            # Try relative URL
                            relative = url.replace('https://www.welcometothejungle.com', '')
                            url_pos = html.find(relative)
                        
                        if url_pos != -1:
                            # Check nearby text (±2000 chars) for location mentions
                            context = html[max(0, url_pos-1000):min(len(html), url_pos+1000)]
                            
                            # Find matching location in nearby context
                            for loc in city_locations:
                                if loc in context or loc.replace(' ', '') in context:
                                    url_to_location[url] = loc
                                    break
                    
                    # Filter by title AND location
                    filtered_urls = []
                    for url in all_urls:
                        # Extract job slug from URL (last part after /jobs/)
                        slug_match = re.search(r'/jobs/([^?#]+)$', url)
                        if not slug_match:
                            continue
                            
                        slug = slug_match.group(1)
                        
                        # Check title match
                        title_matched = False
                        for title in title_matches:
                            if self._match_job_title(job_title, title):
                                # Check if title terms appear in slug
                                slug_lower = slug.lower().replace('-', ' ').replace('_', ' ')
                                title_lower = title.lower().replace('_', '')
                                title_words = [w for w in title_lower.split() if len(w) > 2]
                                slug_words = slug_lower.split()
                                common = sum(1 for w in title_words if w in slug_words)
                                if common >= 2:
                                    title_matched = True
                                    break
                        
                        if not title_matched:
                            continue
                        
                        # Check location match - THREE SOURCES:
                        # 1. URL slug (e.g., _toulouse in URL) - AUTHORITATIVE but rare
                        # 2. Extracted location from HTML context - MAIN METHOD
                        # 3. No filtering if both above fail (trust WTTJ search results)
                        
                        # Check URL slug first (most reliable when present)
                        slug_lower = slug.lower()
                        
                        # REJECT if URL explicitly mentions a DIFFERENT city
                        # (e.g., _paris when searching Toulouse)
                        major_cities = ['paris', 'lyon', 'toulouse', 'nice', 'nantes', 'bordeaux', 'lille', 'rennes', 'montpellier', 'marseille']
                        explicit_other_city = False
                        for other_city in major_cities:
                            if other_city != target_city_lower and f"_{other_city}" in slug_lower:
                                # URL has explicit different city - reject it
                                explicit_other_city = True
                                break
                        
                        if explicit_other_city:
                            continue  # Skip this job
                        
                        # Check if URL has target city explicitly
                        url_has_target_city = f"_{target_city_lower}" in slug_lower
                        
                        # Also check for nearby/metro cities in URL
                        if target_city_lower == 'marseille':
                            url_has_target_city = url_has_target_city or any(
                                f"_{nearby}" in slug_lower for nearby in ['aix', 'aubagne', 'salon']
                            )
                        elif target_city_lower == 'lille':
                            url_has_target_city = url_has_target_city or any(
                                f"_{nearby}" in slug_lower for nearby in ['roubaix', 'tourcoing']
                            )
                        elif target_city_lower == 'lyon':
                            url_has_target_city = url_has_target_city or f"_villeurbanne" in slug_lower
                        
                        if url_has_target_city:
                            filtered_urls.append(url)
                            continue
                        
                        # URL has no city suffix - check extracted location from HTML
                        location = url_to_location.get(url, '')
                        if location:
                            location_lower = location.lower()
                            
                            # Check if target city is in the location string
                            if target_city_lower in location_lower:
                                filtered_urls.append(url)
                                continue
                            
                            # Check for nearby cities in same metro area
                            if target_city_lower == 'marseille' and any(nearby in location_lower for nearby in ['aix', 'aubagne', 'salon']):
                                filtered_urls.append(url)
                                continue
                            elif target_city_lower == 'lille' and any(nearby in location_lower for nearby in ['roubaix', 'tourcoing', 'villeneuve']):  
                                filtered_urls.append(url)
                                continue
                            elif target_city_lower == 'lyon' and 'villeurbanne' in location_lower:
                                filtered_urls.append(url)
                                continue
                        
                        # If we reach here: no city in URL, no location extracted
                        # Trust WTTJ's search results (they filtered by aroundQuery already)
                        # This handles multi-location jobs and edge cases
                        filtered_urls.append(url)
                    
                    print(f"   ✓ Kept {len(filtered_urls)}/{len(all_urls)} WTTJ jobs after title+location filtering")
                    return filtered_urls
                else:
                    print(f"   ⚠️ Firecrawl WTTJ error: {response.status_code}")
                    return []
        except Exception as e:
            print(f"   ⚠️ Firecrawl WTTJ exception: {e}")
            return []

    async def _firecrawl_search_glassdoor(self, job_title: str, city: str, region: str, max_results: int) -> List[str]:
        """
        Search Glassdoor using Firecrawl Scrape on the search results page.
        Optimized for France (.fr) as per user requirements.
        """
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        if not firecrawl_api_key:
            return []
            
        # Construct URL
        # Example: https://www.glassdoor.fr/Job/jobs.htm?sc.keyword=Customer%20Success%20Manager&locKeyword=Marseille
        query_encoded = quote(job_title)
        loc_encoded = quote(city)
        # Using .fr domain
        url = f"https://www.glassdoor.fr/Job/jobs.htm?sc.keyword={query_encoded}&locKeyword={loc_encoded}"
        
        print(f"   🔥 Firecrawl Glassdoor Search: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {firecrawl_api_key}",
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
                    
                    # Extract job links
                    matches = re.findall(r'href=["\']([^"\']*(?:/partner/url/|/job-listing/)[^"\']*)["\']', html)
                    
                    urls = set()
                    for match in matches:
                        if match.startswith('/'):
                            match = f"https://www.glassdoor.fr{match}"
                        urls.add(match)
                        
                    print(f"   ✓ Found {len(urls)} Glassdoor jobs via Firecrawl")
                    return list(urls)
                else:
                    print(f"   ⚠️ Firecrawl Glassdoor error: {response.status_code}")
                    return []
        except Exception as e:
            print(f"   ⚠️ Firecrawl Glassdoor exception: {e}")
            return []

    async def _expand_glassdoor_listings(self, listing_urls: List[str]) -> List[str]:
        """
        Scrape Glassdoor listing pages to extract individual job URLs.
        Uses Firecrawl to handle the scraping.
        """
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        if not firecrawl_api_key or not listing_urls:
            return []

        print(f"   🔥 Expanding {len(listing_urls)} Glassdoor listing pages...")
        
        all_job_urls = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for page_url in listing_urls:
                try:
                    # Use Firecrawl to scrape the listing page
                    scrape_response = await client.post(
                        "https://api.firecrawl.dev/v1/scrape",
                        headers={
                            "Authorization": f"Bearer {firecrawl_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "url": page_url,
                            "formats": ["markdown", "html"],
                            "onlyMainContent": False  # Need full page for job links
                        }
                    )
                    
                    if scrape_response.status_code == 200:
                        scrape_data = scrape_response.json()
                        content = scrape_data.get("data", {})
                        html = content.get("html", "")
                        
                        # Extract job URLs using broader logic
                        # Extract ALL hrefs first
                        all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
                        
                        page_jobs = set()
                        for href in all_hrefs:
                            # Normalize
                            if href.startswith('/'):
                                full_url = f"https://www.glassdoor.com{href}"
                            elif href.startswith('http'):
                                full_url = href
                            else:
                                continue
                                
                            # Check for job patterns
                            # Standard patterns: /partner/url/ or /job-listing/
                            if '/partner/url/' in full_url or '/job-listing/' in full_url:
                                page_jobs.add(full_url)
                            # Fallback: check for generic /job/ patterns but exclude search pages
                            elif '/job/' in full_url.lower() and 'glassdoor.com' in full_url:
                                if 'SRCH_' not in full_url and '/Job/' not in full_url:
                                    page_jobs.add(full_url)
                            
                        if not page_jobs:
                            print(f"      ⚠️ No jobs found in {page_url[:40]}... HTML length: {len(html)}")
                            # Debug: check if we got a captcha or generic page
                            if "captcha" in html.lower() or "verify" in html.lower():
                                print("      ⚠️ Likely CAPTCHA/Bot detection")
                            
                        print(f"      ✓ Extracted {len(page_jobs)} jobs from listing page")
                        all_job_urls.extend(list(page_jobs))
                    else:
                        print(f"      ⚠️ Failed to scrape {page_url[:60]}...: {scrape_response.status_code}")
                        
                except Exception as e:
                    print(f"      ⚠️ Error expanding {page_url[:60]}...: {e}")
                    
        return list(set(all_job_urls))

    async def _unipile_search_linkedin(self, job_title: str, city: str, region: str, max_results: int) -> tuple[List[str], List[Dict]]:
        """
        Search LinkedIn using Unipile Jobs API.
        
        Requires UNIPILE_DSN, UNIPILE_API_KEY, UNIPILE_LINKEDIN_ACCOUNT_ID environment variables.
        Falls back gracefully if not available.
        
        Args:
            job_title: Job title
            city: City
            region: Region
            max_results: Max results to return
            
        Returns:
            Tuple of (List of LinkedIn job URLs, List of full job objects from Unipile)
        """
        unipile_dsn = os.getenv("UNIPILE_DSN")
        unipile_api_key = os.getenv("UNIPILE_API_KEY")
        unipile_account_id = os.getenv("UNIPILE_LINKEDIN_ACCOUNT_ID")
        
        if not all([unipile_dsn, unipile_api_key, unipile_account_id]):
            print(f"   ⚠️  UNIPILE credentials not set, skipping LinkedIn search")
            with open(self.results_dir / "unipile_linkedin.json", "w") as f:
                json.dump({
                    "note": "UNIPILE credentials not configured",
                    "hint": "Set UNIPILE_DSN, UNIPILE_API_KEY, UNIPILE_LINKEDIN_ACCOUNT_ID in .env"
                }, f, indent=2)
            return [], []
        
        try:
            print(f"   🔗 Unipile Jobs API for LinkedIn: '{job_title}' AND '{city}'")
            
            # Force higher limit as requested
            limit = 99 if max_results > 99 else max_results
            
            # Triple Query Strategy: Strict + Loose + TitleOnly (High Recall)
            # Unipile doesn't support 'location' param for jobs, so we must include city in keywords
            # Or filter client-side for broad queries
            queries = [
                {"type": "Strict", "keywords": f'"{job_title}" AND "{city}"', "filter_loc": False},
                {"type": "Loose", "keywords": f"{job_title} {city}", "filter_loc": False},
                # Title Only: High recall for jobs with different location formatting or semantics
                {"type": "TitleOnly", "keywords": f"{job_title}", "filter_loc": True}
            ]
            
            all_job_objects = []
            seen_ids = set()
            urls = []
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                for q in queries:
                    print(f"   🔗 Unipile LinkedIn ({q['type']}): {q['keywords']}")
                    
                    try:
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
                                "keywords": q['keywords'],
                                "limit": limit,
                                "count": limit
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            items = data.get("items", [])
                            count = 0
                            for item in items:
                                if item.get("type") != "JOB":
                                    continue
                                    
                                # Deduplicate by ID
                                job_id = item.get("id")
                                if job_id and job_id in seen_ids:
                                    continue
                                    
                                # If filter_loc is True, check if location matches city/region
                                if q.get("filter_loc"):
                                    loc = item.get("location", "").lower()
                                    # Simple check: is city in location string?
                                    if city.lower() not in loc:
                                        # Maybe check region too if provided?
                                        if region and region.lower() not in loc:
                                            continue
                                
                                if job_id:
                                    seen_ids.add(job_id)
                                
                                url = item.get("job_url") or item.get("url") or item.get("link")
                                if url:
                                    urls.append(url)
                                    all_job_objects.append(item)
                                    count += 1
                            print(f"      ✓ Found {count} new jobs")
                        else:
                            print(f"      ⚠️ Error: {response.status_code}")
                            
                    except Exception as e:
                        print(f"      ⚠️ Exception: {e}")
            
            # Save results
            with open(self.results_dir / "unipile_linkedin.json", "w") as f:
                json.dump({"items": all_job_objects, "count": len(all_job_objects)}, f, indent=2)
            
            print(f"   ✓ Unipile returned {len(all_job_objects)} unique LinkedIn jobs")
            return urls, all_job_objects
                    
        except Exception as e:
            print(f"   ⚠️  Unipile LinkedIn error: {type(e).__name__}: {e}")
            return [], []
    
    async def phase1_search(self, job_title: str, city: str, region: str, limit_per_source: int) -> tuple[List[str], List[Dict]]:
        """
        Phase 1: Multi-source search with URL filtering.
        
        Uses Direct Firecrawl Scraping for Indeed, Glassdoor, WTTJ.
        Uses Unipile for LinkedIn.
        """
        
        # 1. Indeed (Direct)
        print("   🔎 Running Firecrawl Direct Search for Indeed...")
        indeed_urls = await self._firecrawl_search_indeed(job_title, city, region, limit_per_source * 3)
        print(f"   ✓ Firecrawl Indeed: {len(indeed_urls)} URLs")
        
        # 2. WTTJ (Direct)
        print("   🔎 Running Firecrawl Direct Search for WTTJ...")
        wttj_urls = await self._firecrawl_search_wttj(job_title, city, region, limit_per_source * 3)
        print(f"   ✓ Firecrawl WTTJ: {len(wttj_urls)} URLs")
        
        # 3. Glassdoor (Direct)
        print("   🔎 Running Firecrawl Direct Search for Glassdoor...")
        glassdoor_urls = await self._firecrawl_search_glassdoor(job_title, city, region, limit_per_source * 3)
        print(f"   ✓ Firecrawl Glassdoor: {len(glassdoor_urls)} URLs")
        
        # 4. LinkedIn (Unipile)
        print("   🔎 Running Unipile Jobs API for LinkedIn...")
        linkedin_urls, linkedin_job_objects = await self._unipile_search_linkedin(job_title, city, region, limit_per_source * 10)
        
        self.linkedin_job_objects = linkedin_job_objects
        print(f"   💾 Stored {len(linkedin_job_objects)} LinkedIn job objects")
        
        # Merge
        all_urls = indeed_urls + wttj_urls + glassdoor_urls + linkedin_urls
        print(f"   📊 Total raw URLs: {len(all_urls)}")
        
        # Filter (legacy cleanup)
        print("   🔍 Filtering URLs...")
        filtered_urls = self._filter_job_urls(all_urls)
        print(f"   ✅ Filtered to {len(filtered_urls)} job-specific URLs")
        
        # Deduplicate
        unique_urls = list(set(filtered_urls))
        print(f"   🎯 After deduplication: {len(unique_urls)} unique URLs")
        
        # Stats
        gd_count = len([u for u in unique_urls if 'glassdoor' in u.lower()])
        wt_count = len([u for u in unique_urls if 'welcometothejungle' in u.lower()])
        in_count = len([u for u in unique_urls if 'indeed' in u.lower()])
        li_count = len([u for u in unique_urls if 'linkedin' in u.lower()])
        
        print(f"   📍 Final selection: {gd_count} Glassdoor + {wt_count} WTTJ + {in_count} Indeed + {li_count} LinkedIn")
        
        # Return URLs for scraping (excluding LinkedIn which is handled separately)
        scraping_urls = [u for u in unique_urls if 'linkedin' not in u.lower()]
        print(f"   ⚡ Returning {len(scraping_urls)} URLs for scraping (LinkedIn will be handled separately)")
        
        return scraping_urls, linkedin_job_objects
    
    async def _parallel_search_api(self, job_title: str, city: str, region: str, max_results: int) -> List[str]:
        """
        Call Parallel Search API to find job URLs.
        
        Args:
            job_title: Job title
            city: City
            region: Region
            max_results: Max results to return
            
        Returns:
            List of job URLs
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "mode": "agentic",
                    "objective": f"Find {job_title} job postings in {city}, {region}, France on Glassdoor, Welcome to the Jungle, and Indeed",
                    "search_queries": [
                        f"site:fr.indeed.com {job_title} {city} {region}"
                    ],
                    "max_results": max_results,
                    "excerpts": {
                        "max_chars_per_result": 500
                    }
                }
                
                response = await client.post(
                    f"{self.parallel_base_url}/search",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    print(f"   ⚠️ Parallel Search API error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    return []
                
                data = response.json()
                
                # Save raw response
                with open(self.results_dir / "parallel_search.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                # Extract URLs
                urls = []
                for result in data.get("results", []):
                    url = result.get("url")
                    if url:
                        urls.append(url)
                
                return urls
                
        except Exception as e:
            print(f"   ⚠️ Parallel Search error: {type(e).__name__}: {e}")
            return []
    
    def _parse_unipile_jobs(self, unipile_jobs: List[Dict]) -> List[Dict]:
        """
        Parse Unipile LinkedIn job objects into standardized format.
        
        Unipile provides clean structured data directly from LinkedIn API,
        so no scraping/extraction is needed.
        
        Args:
            unipile_jobs: List of job objects from Unipile API
            
        Returns:
            List of structured job dicts
        """
        structured_jobs = []
        
        for job in unipile_jobs:
            # Unipile job object structure:
            # {
            #   "type": "JOB",
            #   "id": "4324396595",
            #   "title": "Enterprise Customer Success Manager (CSM)",
            #   "location": "Greater Marseille Metropolitan Area (Hybrid)",
            #   "posted_at": "2025-11-25T16:43:06.000Z",
            #   "url": "https://www.linkedin.com/jobs/view/4324396595",
            #   "company": {"name": "ORBCOMM", "public_identifier": "orbcomm"}
            # }
            
            # Extract company name from company object or fallback to string
            company = job.get("company", {})
            company_name = company.get("name", "Unknown Company") if isinstance(company, dict) else str(company)
            
            # Parse location for remote/hybrid detection
            location = job.get("location", "Not specified")
            remote = self._extract_remote_type_from_text(location)
            
            # Parse posted date
            posted_at = job.get("posted_at", "")
            posted_date = posted_at.split("T")[0] if posted_at else "Not specified"
            
            structured_job = {
                "title": job.get("title", "Unknown Title"),
                "company": company_name,
                "location": location,
                "salary": "Not specified",  # Unipile doesn't provide salary
                "contract_type": "Not specified",  # Unipile doesn't provide contract type
                "remote": remote,
                "description": f"LinkedIn job posting - Full details available at job URL",  # Unipile doesn't provide full description
                "skills": "Not specified",  # Unipile doesn't provide skills
                "posted_date": posted_date,
                "url": job.get("url", ""),
                "source": "linkedin",
                "extraction_method": "unipile_direct"
            }
            
            structured_jobs.append(structured_job)
            print(f"   ✓ Parsed Unipile job: {structured_job['title']} @ {structured_job['company']}")
        
        return structured_jobs
    
    def _extract_remote_type_from_text(self, text: str) -> str:
        """Extract remote work policy from text."""
        text_lower = text.lower()
        
        if "remote" in text_lower and "hybrid" not in text_lower:
            return "Remote"
        elif "hybrid" in text_lower or "hybride" in text_lower:
            return "Hybrid"
        elif "on-site" in text_lower or "on site" in text_lower:
            return "Onsite"
        
        return "Not specified"
    
    def _firecrawl_extract_jobs(self, urls: List[str]) -> List[Dict]:
        """
        Extract job data from URLs using Firecrawl Extract API.
        
        Uses the Firecrawl Extract API with JSON schema to extract
        structured job posting data from web pages.
        
        Args:
            urls: List of job URLs (recommended max 10 per call)
            
        Returns:
            List of dicts with 'url' and 'structured_data' fields
        """
        if not urls:
            return []
        
        # Get API key from environment
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            print("   ⚠️ FIRECRAWL_API_KEY not found in environment")
            return []
        
        try:
            # Prepare schema for Firecrawl Extract
            schema = {
                "type": "object",
                "properties": {
                    "job_title": {"type": "string", "description": "Job title or position name"},
                    "company_name": {"type": "string", "description": "Company or employer name"},
                    "location": {"type": "string", "description": "Job location (city, region)"},
                    "salary_range": {"type": "string", "description": "Salary range or compensation"},
                    "contract_type": {"type": "string", "description": "Contract type (CDI, CDD, Stage, Alternance, Freelance)"},
                    "remote_work": {"type": "string", "description": "Remote work policy (Remote, Hybrid, Onsite)"},
                    "description": {"type": "string", "description": "Job description and responsibilities"},
                    "skills": {"type": "array", "items": {"type": "string"}, "description": "Required skills and qualifications"},
                    "posted_date": {"type": "string", "description": "Job posting date"}
                },
                "required": ["job_title", "company_name", "location"]
            }
            
            # Call Firecrawl Scrape API with extract format (synchronous, one URL at a time)
            import httpx
            mapped_results = []
            
            with httpx.Client(timeout=120.0) as client:
                for url in urls:
                    try:
                        payload = {
                            "url": url,
                            "formats": ["extract"],
                            "extract": {
                                "prompt": "Extract job posting details including title, company, location, salary, contract type, remote policy, description, required skills, and posting date",
                                "schema": schema
                            }
                        }
                        
                        response = client.post(
                            "https://api.firecrawl.dev/v1/scrape",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json=payload
                        )
                        
                        if response.status_code != 200:
                            print(f"   ⚠️ Firecrawl error for {url[:50]}: {response.status_code}")
                            mapped_results.append({"url": url, "structured_data": {}})
                            continue
                        
                        result = response.json()
                        
                        # Firecrawl scrape returns: {"success": true, "data": {"extract": {...}, ...}}
                        if result.get("success") and result.get("data", {}).get("extract"):
                            extracted = result["data"]["extract"]
                            mapped_results.append({
                                "url": url,
                                "structured_data": extracted
                            })
                        else:
                            mapped_results.append({"url": url, "structured_data": {}})
                            
                    except Exception as e:
                        print(f"   ⚠️ Firecrawl error for {url[:50]}: {e}")
                        mapped_results.append({"url": url, "structured_data": {}})
            
            return mapped_results
            
        except Exception as e:
            print(f"   ⚠️ Firecrawl Extract error: {type(e).__name__}: {e}")
            return []
    
    async def phase2_extract(self, urls: List[str]) -> Optional[Dict]:
        """
        Phase 2: Extract content from URLs using Firecrawl Extract MCP.
        Handles batching (10 URLs per batch recommended for Firecrawl).
        
        Args:
            urls: List of job URLs
            
        Returns:
            Extract results dict or None
        """
        print(f"   🔍 Extracting content from {len(urls)} URLs using Firecrawl...")
        
        all_results = []
        batch_size = 10  # Conservative batch size for Firecrawl
        
        # Split URLs into batches
        batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]
        
        for i, batch in enumerate(batches):
            if len(batches) > 1:
                print(f"   📦 Processing batch {i+1}/{len(batches)} ({len(batch)} URLs)...")
            
            try:
                # Call Firecrawl Extract helper
                batch_results = self._firecrawl_extract_jobs(batch)
                
                if batch_results:
                    all_results.extend(batch_results)
                    print(f"   ✓ Extracted {len(batch_results)} pages from batch {i+1}")
                else:
                    print(f"   ⚠️ Firecrawl returned no results for batch {i+1}")
                    
            except Exception as e:
                print(f"   ⚠️ Firecrawl Extract error (batch {i+1}): {type(e).__name__}: {e}")
        
        if not all_results:
            return None
            
        return {"results": all_results}
    
    def _validate_field(self, field_name: str, value: str) -> str:
        """
        Validate and clean extracted field values.
        Rejects navigation text, invalid data, and returns cleaned value or empty string.
        
        Args:
            field_name: Name of field being validated (title, company, salary, etc.)
            value: Raw extracted value
            
        Returns:
            Cleaned value or empty string if invalid
        """
        if not value or not isinstance(value, str):
            return ""
        
        value = value.strip()
        
        # Common navigation/UI text to reject
        navigation_keywords = [
            "skip to", "sign in", "sign up", "cookie", "accept", "close",
            "continue without", "upload your resume", "create alert",
            "notifications", "search", "menu", "home", "jobs", "companies",
            "salaries", "reviews", "for employers", "main content",
            "start of main", "end of main", "scroll to"
        ]
        
        value_lower = value.lower()
        
        # Reject if contains navigation keywords
        if any(keyword in value_lower for keyword in navigation_keywords):
            return ""
        
        # Field-specific validation
        if field_name == "title":
            # Reject if too short (< 5 chars) or too long (> 150 chars)
            if len(value) < 5 or len(value) > 150:
                return ""
            # Reject common non-title values
            if value_lower in ["cdi", "cdd", "stage", "content:", "section title:"]:
                return ""
        
        elif field_name == "company":
            # Reject if too short (< 2 chars)
            if len(value) < 2:
                return ""
            # Reject common non-company values
            invalid_companies = ["reviews", "jobs", "salaries", "companies", ";", "unknown company"]
            if value_lower in invalid_companies:
                return ""
        
        elif field_name == "salary":
            # Reject if looks like a date range (YYYY-YYYY)
            if re.match(r"^\d{4}-\d{4}$", value):
                return ""
            # Reject if contains copyright symbol
            if "©" in value or "copyright" in value_lower:
                return ""
        
        return value
    
    def phase3_structure(self, extract_results: Dict, linkedin_jobs: List[Dict] = None) -> List[Dict]:
        """
        Phase 3: Structure extracted data into standardized format.
        Merges scraped jobs with LinkedIn jobs from Unipile.
        
        Args:
            extract_results: Results from Parallel Extract API
            linkedin_jobs: Optional list of LinkedIn jobs from Unipile (pre-parsed)
            
        Returns:
            List of structured job dicts
        """
        structured_jobs = []
        
        # Process scraped jobs (Glassdoor, WTTJ, Indeed)
        for result in extract_results.get("results", []):
            url = result.get("url", "")
            
            # Try to get structured_data from schema extraction first
            structured_data = result.get("structured_data", {})
            
            if structured_data:
                # Extract from schema (primary method)
                title = self._validate_field("title", structured_data.get("job_title", ""))
                company = self._validate_field("company", structured_data.get("company_name", ""))
                location = structured_data.get("location", "")
                salary = self._validate_field("salary", structured_data.get("salary_range", ""))
                contract_type = structured_data.get("contract_type", "")
                remote = structured_data.get("remote_work", "")
                description = structured_data.get("description", "")
                skills_list = structured_data.get("skills", [])
                skills = ", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list)
                posted_date = structured_data.get("posted_date", "")
                extraction_method = "firecrawl_extract"
            else:
                # Fallback to regex parsing (legacy method)
                # Combine excerpts and full content for parsing
                content = ""
                if result.get("excerpts"):
                    content += " ".join(result["excerpts"])
                if result.get("full_content"):
                    content += " " + result["full_content"]
                
                if not content:
                    print(f"   ⚠️ No content for {url}")
                    continue
                
                # Parse with regex heuristics
                title = self._validate_field("title", self._extract_field(content, "title", result.get("title", "")))
                company = self._validate_field("company", self._extract_field(content, "company"))
                location = self._extract_field(content, "location")
                salary = self._validate_field("salary", self._extract_salary(content))
                contract_type = self._extract_contract_type(content)
                remote = self._extract_remote_type(content)
                description = content[:500] + "..." if len(content) > 500 else content
                skills = self._extract_skills(content)
                posted_date = self._extract_date(content)
                extraction_method = "regex_fallback"
            
            # Use fallbacks for empty fields
            if not title:
                title = "Unknown Title"
            if not company:
                company = "Unknown Company"
            if not location:
                location = "Unknown Location"
            if not salary:
                salary = "Not specified"
            if not contract_type:
                contract_type = "Not specified"
            if not remote:
                remote = "Not specified"
            if not skills:
                skills = "Not specified"
            if not posted_date:
                posted_date = "Not specified"
            
            job = {
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "contract_type": contract_type,
                "remote": remote,
                "description": description[:500] + "..." if len(description) > 500 else description,
                "skills": skills,
                "posted_date": posted_date,
                "url": url,
                "source": (
                    "glassdoor" if "glassdoor.com" in url.lower()
                    else "indeed" if "indeed.com" in url.lower()
                    else "linkedin" if "linkedin.com" in url.lower()
                    else "wttj"
                ),
                "extraction_method": extraction_method
            }
            
            structured_jobs.append(job)
            print(f"   ✓ Structured: {job['title']} @ {job['company']} [{extraction_method}]")
        
        # Merge LinkedIn jobs from Unipile (if provided)
        if linkedin_jobs:
            print(f"\n   🔗 Merging {len(linkedin_jobs)} LinkedIn jobs from Unipile...")
            structured_jobs.extend(linkedin_jobs)
        
        # Save all structured jobs (including LinkedIn)
        with open(self.results_dir / "jobs.json", "w") as f:
            json.dump(structured_jobs, f, indent=2, ensure_ascii=False)
        
        return structured_jobs
    
    def _extract_field(self, content: str, field: str, fallback: str = "") -> str:
        """Extract a specific field from content using heuristics."""
        content_lower = content.lower()
        
        if field == "title":
            # Look for job title patterns
            patterns = [
                r"(?:job title|position|poste)[:\s]+([^\n]+)",
                r"^([A-Z][^\n]{10,60})\n",
            ]
            for pattern in patterns:
                match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return fallback or "Unknown Title"
        
        elif field == "company":
            patterns = [
                r"(?:company|entreprise|société)[:\s]+([^\n]+)",
                r"chez\s+([A-Z][^\n\.;]{2,40})",
                r"@\s*([A-Z][^\n]{2,40})",
            ]
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return "Unknown Company"
        
        elif field == "location":
            # Improved location extraction
            location_patterns = [
                r"(?:lieu|location|localisation|ville)\s*[:\-]\s*([^\n\.;]{3,50})",
                r"(?:à|in)\s+(Lyon|Paris|Bordeaux|Marseille|Toulouse|Nantes|Nice|Grenoble|Strasbourg|Rennes|Lille)[,\s\.]?",
                r"(Lyon|Paris|Bordeaux|Marseille|Toulouse|Nantes|Nice|Grenoble|Strasbourg|Rennes|Lille)\s*(?:\([0-9]{2}\)|,|\.|$)",
            ]
            for pattern in location_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    loc = match.group(1).strip()
                    # Clean up
                    loc = re.sub(r'\s+', ' ', loc)
                    loc = loc.split('.')[0].split(';')[0]
                    return loc
            
            # Fallback to detecting city names
            major_cities = ['Lyon', 'Paris', 'Bordeaux', 'Marseille', 'Toulouse', 'Nantes', 'Nice', 'Grenoble', 'Strasbourg', 'Rennes', 'Lille']
            for city in major_cities:
                if city.lower() in content_lower:
                    return city
                    
            return "Unknown Location"
        
        return ""
    
    def _extract_salary(self, content: str) -> str:
        """Extract salary information."""
        patterns = [
            r"(€?\s*\d{1,3}[,\s]?\d{3}\s*[-–]\s*€?\s*\d{1,3}[,\s]?\d{3})",
            r"(\d{2,3}k\s*[-–]\s*\d{2,3}k)",
            r"(salaire[:\s]+[^\n]{10,50})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Not specified"
    
    def _extract_contract_type(self, content: str) -> str:
        """Extract contract type (CDI, CDD, Stage, etc.)."""
        content_lower = content.lower()
        
        if "cdi" in content_lower:
            return "CDI"
        elif "cdd" in content_lower:
            return "CDD"
        elif "stage" in content_lower or "internship" in content_lower:
            return "Stage"
        elif "alternance" in content_lower or "apprenticeship" in content_lower:
            return "Alternance"
        elif "freelance" in content_lower:
            return "Freelance"
        
        return "Not specified"
    
    def _extract_remote_type(self, content: str) -> str:
        """Extract remote work policy."""
        content_lower = content.lower()
        
        if "full remote" in content_lower or "100% remote" in content_lower or "télétravail complet" in content_lower:
            return "Remote"
        elif "hybrid" in content_lower or "hybride" in content_lower or "télétravail partiel" in content_lower:
            return "Hybrid"
        elif "on-site" in content_lower or "sur site" in content_lower or "présentiel" in content_lower:
            return "Onsite"
        elif "remote" in content_lower or "télétravail" in content_lower:
            return "Remote/Hybrid"
        
        return "Not specified"
    
    def _extract_skills(self, content: str) -> str:
        """Extract required skills."""
        # Common PM skills to look for
        skill_keywords = [
            "agile", "scrum", "kanban", "jira", "product roadmap", 
            "user stories", "stakeholder", "analytics", "sql", "python",
            "figma", "sketch", "ux", "ui", "api", "saas", "b2b", "b2c"
        ]
        
        found_skills = []
        content_lower = content.lower()
        
        for skill in skill_keywords:
            if skill in content_lower:
                found_skills.append(skill)
        
        return ", ".join(found_skills) if found_skills else "Not specified"
    
    def _extract_date(self, content: str) -> str:
        """Extract posting date."""
        date_patterns = [
            r"(?:posted|publié|date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})",
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Not specified"
    
    def export_csv(self, jobs: List[Dict]) -> Path:
        """
        Export structured jobs to CSV.
        
        Args:
            jobs: List of structured job dicts
            
        Returns:
            Path to CSV file
        """
        csv_path = self.results_dir / "jobs.csv"
        
        fieldnames = [
            "title", "company", "location", "salary", "contract_type",
            "remote", "description", "skills", "posted_date",
            "url", "source", "extraction_method"
        ]
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)
        
        print(f"   ✓ CSV exported: {csv_path}")
        return csv_path


async def main():
    """Main entry point."""
    # Parse command-line arguments
    if len(sys.argv) >= 4:
        JOB_TITLE = sys.argv[1]
        CITY = sys.argv[2]
        REGION = sys.argv[3]
        LIMIT_PER_SOURCE = int(sys.argv[4]) if len(sys.argv) >= 5 else 3
    else:
        # Default values if no args provided
        JOB_TITLE = "Product Manager"
        CITY = "Bordeaux"
        REGION = "Nouvelle-Aquitaine"
        LIMIT_PER_SOURCE = 3
    
    # Configuration
    PARALLEL_API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"
    
    # Run scraper
    scraper = ParallelScraper(api_key=PARALLEL_API_KEY)
    
    try:
        csv_path = await scraper.run(
            job_title=JOB_TITLE,
            city=CITY,
            region=REGION,
            limit_per_source=LIMIT_PER_SOURCE
        )
        
        if csv_path:
            print(f"\n✅ Done! Check {csv_path}")
        else:
            print("\n❌ Scraping failed.")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
