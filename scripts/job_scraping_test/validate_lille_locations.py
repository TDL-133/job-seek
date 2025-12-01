#!/usr/bin/env python3
"""
Validate job locations from Phase 1 URLs.

This script scrapes each job URL to extract and validate the actual job location.
It determines whether jobs are truly located in Lille or are from other cities.
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional
import sys
import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple scraper without app dependencies
class SimpleScraper:
    """Simple web scraper using httpx."""
    
    def __init__(self):
        self.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
        self.firecrawl_url = "https://api.firecrawl.dev/v1/scrape"
    
    async def scrape_url(self, url: str) -> str:
        """Scrape a URL using Firecrawl or fallback to httpx."""
        # Try Firecrawl first if API key available
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
        
        # Fallback to simple httpx
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                return response.text
        except Exception as e:
            print(f"    Scraping failed: {e}")
            return ""


class LocationValidator:
    """Validates job locations by scraping URLs."""
    
    def __init__(self):
        self.scraper = SimpleScraper()
        self.lille_keywords = {
            "lille", "villeneuve-d'ascq", "roubaix", "tourcoing", 
            "marcq-en-baroeul", "lambersart", "hellemmes", "lomme",
            "métropole lilloise", "metropole lilloise", "mel"
        }
        self.french_cities = {
            "paris", "lyon", "marseille", "toulouse", "nantes", 
            "nice", "bordeaux", "strasbourg", "rennes", "grenoble",
            "montpellier", "aix-en-provence"
        }
    
    def extract_location_from_content(self, content: str, url: str) -> Dict[str, any]:
        """
        Extract location information from job content.
        
        Returns:
            Dict with 'location', 'is_lille', 'is_remote', 'confidence'
        """
        content_lower = content.lower()
        
        # Check for Lille
        lille_mentions = sum(1 for kw in self.lille_keywords if kw in content_lower)
        
        # Check for other cities
        other_city_mentions = sum(1 for city in self.french_cities if city in content_lower)
        
        # Check for remote
        remote_keywords = ["remote", "télétravail", "teletravail", "full remote", "100% remote"]
        is_remote = any(kw in content_lower for kw in remote_keywords)
        
        # Try to extract explicit location from common patterns
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
                extracted_location = match.group(1).strip()[:100]  # Limit length
                break
        
        # Determine if it's Lille-based
        if lille_mentions >= 2:
            is_lille = True
            confidence = "high"
        elif lille_mentions == 1 and other_city_mentions == 0:
            is_lille = True
            confidence = "medium"
        elif lille_mentions == 1 and other_city_mentions > 0:
            is_lille = False
            confidence = "medium"
        elif lille_mentions == 0 and other_city_mentions > 0:
            is_lille = False
            confidence = "high"
        else:
            is_lille = False
            confidence = "low"
        
        return {
            "location": extracted_location,
            "is_lille": is_lille,
            "is_remote": is_remote,
            "confidence": confidence,
            "lille_mentions": lille_mentions,
            "other_city_mentions": other_city_mentions
        }
    
    async def validate_url(self, url: str, platform: str) -> Dict[str, any]:
        """Validate a single job URL."""
        try:
            print(f"  Scraping: {url[:80]}...")
            
            # Scrape the URL
            content = await self.scraper.scrape_url(url)
            
            if not content:
                return {
                    "url": url,
                    "platform": platform,
                    "status": "error",
                    "error": "Failed to scrape content"
                }
            
            # Extract location info
            location_info = self.extract_location_from_content(content, url)
            
            return {
                "url": url,
                "platform": platform,
                "status": "success",
                **location_info
            }
            
        except Exception as e:
            return {
                "url": url,
                "platform": platform,
                "status": "error",
                "error": str(e)
            }
    
    async def validate_batch(self, urls: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """Validate a batch of URLs."""
        tasks = [self.validate_url(job["url"], job["platform"]) for job in urls]
        results = await asyncio.gather(*tasks)
        return results


def parse_phase1_urls(filepath: str) -> List[Dict[str, str]]:
    """Parse the phase1_urls.md file."""
    jobs = []
    current_platform = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Platform headers
            if line.startswith("## "):
                platform_match = re.match(r'## (\w+)', line)
                if platform_match:
                    current_platform = platform_match.group(1)
            
            # Job URLs
            elif line.startswith("- https://"):
                url = line.split()[1]
                if current_platform:
                    jobs.append({
                        "url": url,
                        "platform": current_platform
                    })
    
    return jobs


async def main():
    """Main validation function."""
    
    # Parse Phase 1 URLs
    urls_file = Path(__file__).parent / "phase1_urls.md"
    
    if not urls_file.exists():
        print(f"Error: {urls_file} not found!")
        return
    
    print("📋 Parsing Phase 1 URLs...")
    jobs = parse_phase1_urls(str(urls_file))
    print(f"Found {len(jobs)} jobs to validate\n")
    
    # Validate locations
    validator = LocationValidator()
    
    print("🔍 Validating job locations...\n")
    
    # Process by platform for better organization
    platforms = ["LinkedIn", "Glassdoor", "Indeed"]
    all_results = []
    
    for platform in platforms:
        platform_jobs = [j for j in jobs if j["platform"] == platform]
        if not platform_jobs:
            continue
        
        print(f"\n{'='*60}")
        print(f"Platform: {platform} ({len(platform_jobs)} jobs)")
        print('='*60)
        
        results = await validator.validate_batch(platform_jobs)
        all_results.extend(results)
        
        # Show summary for this platform
        lille_jobs = [r for r in results if r.get("is_lille")]
        remote_jobs = [r for r in results if r.get("is_remote")]
        errors = [r for r in results if r.get("status") == "error"]
        
        print(f"\n✅ Lille-based: {len(lille_jobs)}")
        print(f"🌍 Remote: {len(remote_jobs)}")
        print(f"❌ Errors: {len(errors)}")
    
    # Final summary
    print(f"\n\n{'='*60}")
    print("FINAL SUMMARY")
    print('='*60)
    
    lille_results = [r for r in all_results if r.get("is_lille")]
    remote_results = [r for r in all_results if r.get("is_remote")]
    other_results = [r for r in all_results if not r.get("is_lille") and not r.get("is_remote") and r.get("status") == "success"]
    errors = [r for r in all_results if r.get("status") == "error"]
    
    print(f"\n📊 Total jobs: {len(all_results)}")
    print(f"✅ Lille-based: {len(lille_results)} ({len(lille_results)/len(all_results)*100:.1f}%)")
    print(f"🌍 Remote: {len(remote_results)} ({len(remote_results)/len(all_results)*100:.1f}%)")
    print(f"🏙️  Other cities: {len(other_results)} ({len(other_results)/len(all_results)*100:.1f}%)")
    print(f"❌ Errors: {len(errors)} ({len(errors)/len(all_results)*100:.1f}%)")
    
    # Show Lille jobs details
    if lille_results:
        print(f"\n{'='*60}")
        print(f"LILLE JOBS ({len(lille_results)} total)")
        print('='*60)
        
        for r in lille_results:
            print(f"\n🎯 {r['platform']}")
            print(f"   URL: {r['url'][:80]}...")
            print(f"   Location: {r.get('location', 'N/A')}")
            print(f"   Confidence: {r['confidence']}")
            print(f"   Mentions: Lille={r['lille_mentions']}, Other={r['other_city_mentions']}")
    
    # Save detailed results
    output_file = Path(__file__).parent / "lille_validation_results.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Lille Job Location Validation Results\n\n")
        f.write(f"**Total Jobs**: {len(all_results)}\n")
        f.write(f"**Lille-based**: {len(lille_results)} ({len(lille_results)/len(all_results)*100:.1f}%)\n")
        f.write(f"**Remote**: {len(remote_results)} ({len(remote_results)/len(all_results)*100:.1f}%)\n")
        f.write(f"**Other cities**: {len(other_results)} ({len(other_results)/len(all_results)*100:.1f}%)\n")
        f.write(f"**Errors**: {len(errors)} ({len(errors)/len(all_results)*100:.1f}%)\n\n")
        
        # Lille jobs
        f.write(f"## ✅ Lille-based Jobs ({len(lille_results)})\n\n")
        for r in lille_results:
            f.write(f"### {r['platform']}\n")
            f.write(f"- **URL**: {r['url']}\n")
            f.write(f"- **Location**: {r.get('location', 'N/A')}\n")
            f.write(f"- **Confidence**: {r['confidence']}\n")
            f.write(f"- **Remote**: {r['is_remote']}\n")
            f.write(f"- **Mentions**: Lille={r['lille_mentions']}, Other={r['other_city_mentions']}\n\n")
        
        # Remote jobs
        f.write(f"## 🌍 Remote Jobs ({len(remote_results)})\n\n")
        for r in remote_results:
            if not r.get('is_lille'):  # Don't duplicate Lille remote jobs
                f.write(f"- {r['platform']}: {r['url']}\n")
        
        # Other cities
        f.write(f"\n## 🏙️ Other Cities ({len(other_results)})\n\n")
        for r in other_results:
            f.write(f"- {r['platform']}: {r['url']}\n")
    
    print(f"\n\n💾 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
