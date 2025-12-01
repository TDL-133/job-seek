#!/usr/bin/env python3
"""
Phase 2: Job Details Extraction & Location Validation

Reads Phase 1 URLs, scrapes each job posting to extract full details,
validates location (target city + remote detection), outputs structured data.

Input: phase1_urls.json
Output: phase2_jobs.json, phase2_jobs.csv
"""

import asyncio
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv

load_dotenv()


class JobExtractor:
    """Extracts detailed job information from URLs."""
    
    def __init__(self, target_city: str):
        self.target_city = target_city.lower()
        self.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
        self.firecrawl_url = "https://api.firecrawl.dev/v1/scrape"
        
        # Location keywords for target city
        self.city_variations = self._get_city_variations(target_city)
        
        # French cities for filtering
        self.other_cities = {
            "paris", "lyon", "marseille", "toulouse", "nantes",
            "nice", "bordeaux", "strasbourg", "rennes", "grenoble",
            "montpellier", "aix-en-provence"
        }
        self.other_cities.discard(self.target_city)
    
    def _get_city_variations(self, city: str) -> set:
        """Get variations of city name including metro area."""
        city_lower = city.lower()
        variations = {city_lower}
        
        # Add metro area variations
        if city_lower == "lille":
            variations.update([
                "villeneuve-d'ascq", "roubaix", "tourcoing",
                "marcq-en-baroeul", "lambersart", "hellemmes", "lomme",
                "métropole lilloise", "metropole lilloise", "mel"
            ])
        elif city_lower == "lyon":
            variations.update([
                "villeurbanne", "vénissieux", "caluire-et-cuire",
                "métropole de lyon", "metropole de lyon"
            ])
        elif city_lower == "marseille":
            variations.update([
                "aix-en-provence", "aubagne", "salon-de-provence",
                "métropole aix-marseille-provence"
            ])
        
        return variations
    
    async def scrape_url(self, url: str) -> str:
        """Scrape a URL using Firecrawl or fallback to httpx."""
        # Try Firecrawl first
        if self.firecrawl_api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.firecrawl_url,
                        json={
                            "url": url,
                            "formats": ["markdown"]
                        },
                        headers={"Authorization": f"Bearer {self.firecrawl_api_key}"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success") and data.get("data"):
                            return data["data"].get("markdown", "")
            except Exception as e:
                print(f"    Firecrawl failed: {e}, trying fallback...")
        
        # Fallback to httpx
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                return response.text
        except Exception as e:
            print(f"    Scraping failed: {e}")
            return ""
    
    def extract_location_info(self, content: str) -> Dict[str, any]:
        """Extract and validate location information."""
        content_lower = content.lower()
        
        # Count mentions
        city_mentions = sum(1 for kw in self.city_variations if kw in content_lower)
        other_city_mentions = sum(1 for city in self.other_cities if city in content_lower)
        
        # Check for remote
        remote_keywords = ["remote", "télétravail", "teletravail", "full remote", "100% remote", "100% télétravail"]
        is_remote = any(kw in content_lower for kw in remote_keywords)
        
        # Extract explicit location
        location_patterns = [
            r'location[:\s]+([^\n<]+)',
            r'lieu[:\s]+([^\n<]+)',
            r'localisation[:\s]+([^\n<]+)',
            r'basé[e]?\s+à\s+([^\n<,]+)',
            r'poste\s+basé\s+à\s+([^\n<,]+)',
        ]
        
        extracted_location = None
        for pattern in location_patterns:
            match = re.search(pattern, content_lower)
            if match:
                extracted_location = match.group(1).strip()[:100]
                break
        
        # Determine if in target city
        if city_mentions >= 2:
            is_target_city = True
            confidence = "high"
        elif city_mentions == 1 and other_city_mentions == 0:
            is_target_city = True
            confidence = "medium"
        elif city_mentions == 1 and other_city_mentions > 0:
            is_target_city = False
            confidence = "medium"
        elif city_mentions == 0 and other_city_mentions > 0:
            is_target_city = False
            confidence = "high"
        else:
            is_target_city = False
            confidence = "low"
        
        # Determine location tag
        if is_target_city and is_remote:
            location_tag = f"{self.target_city.title()}-Remote"
        elif is_target_city:
            location_tag = self.target_city.title()
        elif is_remote:
            location_tag = "Remote"
        else:
            location_tag = "Other"
        
        return {
            "location": extracted_location or "Unknown",
            "is_target_city": is_target_city,
            "is_remote": is_remote,
            "location_tag": location_tag,
            "confidence": confidence,
            "city_mentions": city_mentions,
            "other_city_mentions": other_city_mentions
        }
    
    def extract_job_fields(self, content: str, url: str, platform: str) -> Dict[str, any]:
        """Extract all job fields from content."""
        content_lower = content.lower()
        
        # Title (try to extract from common patterns)
        title = "Unknown"
        title_patterns = [
            r'# ([^\n]+)',  # H1 markdown
            r'title[:\s]+([^\n<]+)',
            r'poste[:\s]+([^\n<]+)',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, content[:1000])  # Search first 1000 chars
            if match:
                title = match.group(1).strip()
                break
        
        # Company
        company = "Unknown"
        company_patterns = [
            r'company[:\s]+([^\n<]+)',
            r'entreprise[:\s]+([^\n<]+)',
            r'société[:\s]+([^\n<]+)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, content_lower[:2000])
            if match:
                company = match.group(1).strip().title()
                break
        
        # Salary
        salary = None
        salary_pattern = r'(\d{1,3}[\s,]\d{3}|\d{2,3}k)[\s€]*(?:[-à]\s*(\d{1,3}[\s,]\d{3}|\d{2,3}k))?'
        salary_match = re.search(salary_pattern, content_lower)
        if salary_match:
            salary = salary_match.group(0).strip()
        
        # Contract type
        contract_type = None
        if any(kw in content_lower for kw in ["cdi", "contrat à durée indéterminée"]):
            contract_type = "CDI"
        elif any(kw in content_lower for kw in ["cdd", "contrat à durée déterminée"]):
            contract_type = "CDD"
        elif any(kw in content_lower for kw in ["stage", "internship"]):
            contract_type = "Stage"
        elif any(kw in content_lower for kw in ["alternance", "apprentissage"]):
            contract_type = "Alternance"
        
        # Description (first 500 chars of cleaned content)
        description = content[:500].replace('\n', ' ').strip()
        
        # Skills (look for bullet points or commas)
        skills = []
        skills_section = re.search(r'(compétences|skills|requirements)[:\s]+([^\n#]{100,500})', content_lower)
        if skills_section:
            skills_text = skills_section.group(2)
            # Split by common delimiters
            skills = [s.strip() for s in re.split(r'[,;•\-]', skills_text) if len(s.strip()) > 2][:10]
        
        return {
            "title": title,
            "company": company,
            "salary": salary,
            "contract_type": contract_type,
            "description": description,
            "skills": skills,
            "url": url,
            "platform": platform
        }
    
    async def extract_job(self, job_url: Dict[str, str]) -> Optional[Dict[str, any]]:
        """Extract complete job information from a URL."""
        url = job_url["url"]
        platform = job_url["platform"]
        
        try:
            print(f"  📄 {platform}: {url[:60]}...")
            
            # Scrape content
            content = await self.scrape_url(url)
            
            if not content:
                return None
            
            # Extract fields
            job_fields = self.extract_job_fields(content, url, platform)
            location_info = self.extract_location_info(content)
            
            # Combine all data
            job_data = {
                **job_fields,
                **location_info,
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            return job_data
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None
    
    async def extract_batch(self, job_urls: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """Extract jobs in batch with delays."""
        jobs = []
        
        for i, job_url in enumerate(job_urls, 1):
            print(f"\n[{i}/{len(job_urls)}] Extracting job...")
            
            job_data = await self.extract_job(job_url)
            if job_data:
                jobs.append(job_data)
            
            # Rate limiting
            if i < len(job_urls):
                await asyncio.sleep(2)
        
        return jobs


def load_phase1_urls(filepath: str) -> List[Dict[str, str]]:
    """Load URLs from Phase 1 JSON output."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get("jobs", [])


def save_json(data: List[Dict], filepath: str):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_csv(data: List[Dict], filepath: str):
    """Save data to CSV file."""
    if not data:
        return
    
    # Define column order
    columns = [
        "title", "company", "location", "location_tag", "salary",
        "contract_type", "is_remote", "description", "skills",
        "url", "platform", "confidence", "city_mentions", "other_city_mentions"
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        
        for job in data:
            # Convert skills list to string
            row = job.copy()
            if isinstance(row.get('skills'), list):
                row['skills'] = ', '.join(row['skills'])
            writer.writerow({k: row.get(k, '') for k in columns})


async def main():
    """Main extraction function."""
    import sys
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python extract_job_details.py <target_city> [phase1_json_path]")
        print("Example: python extract_job_details.py Lille")
        print("         python extract_job_details.py Lyon results/phase1_urls.json")
        return
    
    target_city = sys.argv[1]
    phase1_file = sys.argv[2] if len(sys.argv) >= 3 else "phase1_urls.json"
    
    # Check input file
    if not Path(phase1_file).exists():
        print(f"❌ Error: {phase1_file} not found!")
        print("Run Phase 1 first (parallel_scraper.py)")
        return
    
    print(f"{'='*60}")
    print("PHASE 2: JOB DETAILS EXTRACTION")
    print(f"{'='*60}")
    print(f"Target City: {target_city}")
    print(f"Input: {phase1_file}")
    print()
    
    # Load Phase 1 URLs
    job_urls = load_phase1_urls(phase1_file)
    print(f"📋 Loaded {len(job_urls)} URLs from Phase 1\n")
    
    # Extract jobs
    extractor = JobExtractor(target_city)
    jobs = await extractor.extract_batch(job_urls)
    
    # Summary
    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}")
    
    total = len(jobs)
    target_city_jobs = [j for j in jobs if j["is_target_city"]]
    remote_jobs = [j for j in jobs if j["is_remote"]]
    target_remote = [j for j in target_city_jobs if j["is_remote"]]
    
    print(f"\n📊 Total jobs extracted: {total}")
    print(f"✅ {target_city} jobs: {len(target_city_jobs)} ({len(target_city_jobs)/total*100:.1f}%)")
    print(f"🌍 Remote jobs: {len(remote_jobs)} ({len(remote_jobs)/total*100:.1f}%)")
    print(f"🏠 {target_city} + Remote: {len(target_remote)}")
    
    # Breakdown by tag
    print(f"\n📍 Location Tags:")
    tags = {}
    for job in jobs:
        tag = job["location_tag"]
        tags[tag] = tags.get(tag, 0) + 1
    for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True):
        print(f"   {tag}: {count}")
    
    # Save outputs
    output_dir = Path(phase1_file).parent
    json_path = output_dir / "phase2_jobs.json"
    csv_path = output_dir / "phase2_jobs.csv"
    
    save_json(jobs, str(json_path))
    save_csv(jobs, str(csv_path))
    
    print(f"\n💾 Outputs saved:")
    print(f"   JSON: {json_path}")
    print(f"   CSV: {csv_path}")
    
    print(f"\n✅ Phase 2 complete! Run Phase 3 for scoring.")


if __name__ == "__main__":
    asyncio.run(main())
