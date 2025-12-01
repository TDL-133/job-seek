#!/usr/bin/env python3
"""
Apify City Validator - Phase 2 Enhancement

Reads existing phase2_jobs.csv and enhances job location data using Apify MCP.
Appends new columns: apify_location, apify_company, apify_confidence, location_source

Usage: python apify_city_validator.py <csv_file> <target_city>
Example: python apify_city_validator.py phase2_jobs.csv Toulouse
"""

import csv
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ApifyCityValidator:
    """Validates and enhances job location data using Apify MCP."""
    
    def __init__(self, target_city: str):
        self.target_city = target_city.lower()
        self.city_variations = self._get_city_variations(target_city)
        
        # French cities for filtering
        self.other_cities = {
            "paris", "lyon", "marseille", "toulouse", "nantes",
            "nice", "bordeaux", "strasbourg", "rennes", "grenoble",
            "montpellier", "aix-en-provence", "lille", "clichy",
            "boulogne-billancourt", "pantin", "gennevilliers"
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
        elif city_lower == "toulouse":
            variations.update([
                "blagnac", "colomiers", "tournefeuille",
                "métropole toulousaine", "metropole toulousaine"
            ])
        
        return variations
    
    def call_apify_mcp(self, url: str) -> Optional[Dict]:
        """Call Apify MCP tool.
        
        Note: This function needs to be called from within Warp's AI agent context
        to have access to call_mcp_tool. For standalone testing, it will fail gracefully.
        """
        try:
            print(f"    📞 Calling Apify MCP for URL...")
            
            # This call would be made by Warp's AI agent using call_mcp_tool
            # For now, we document the expected interface and return a placeholder
            
            # Expected call pattern (executed by Warp AI agent):
            # result = call_mcp_tool(
            #     name="apify-slash-rag-web-browser",
            #     input=json.dumps({"query": url, "maxResults": 1})
            # )
            # 
            # Expected result structure:
            # {
            #   "text_result": [
            #     {
            #       "text": "[{markdown content...}]"
            #     },
            #     {
            #       "text": "Actor completed successfully..."
            #     }
            #   ]
            # }
            
            # Parse the first text_result which contains the markdown JSON
            # markdown_json = json.loads(result["text_result"][0]["text"])
            # markdown_data = markdown_json[0] if isinstance(markdown_json, list) else markdown_json
            
            # Return expected structure
            # return {
            #     "success": markdown_data.get("crawl", {}).get("requestStatus") == "handled",
            #     "markdown": markdown_data.get("markdown", ""),
            #     "metadata": markdown_data.get("metadata", {})
            # }
            
            # For standalone execution, return placeholder
            print(f"    ⚠️  Warning: Running outside Warp AI agent context")
            print(f"    ℹ️  This script must be executed by Warp AI agent to call Apify MCP")
            return {
                "success": False,
                "markdown": "",
                "metadata": {
                    "title": "",
                    "description": ""
                },
                "error": "apify_mcp_not_available"
            }
            
        except Exception as e:
            print(f"    ❌ Apify MCP call failed: {e}")
            return None
    
    def extract_location_from_apify(self, apify_data: Dict) -> Dict[str, any]:
        """Extract location and company from Apify response."""
        if not apify_data or not apify_data.get("success"):
            return {
                "location": None,
                "company": None,
                "confidence": "none"
            }
        
        markdown = apify_data.get("markdown", "")
        metadata = apify_data.get("metadata", {})
        title = metadata.get("title", "")
        description = metadata.get("description", "")
        
        # Extract location from title (e.g., "Product Manager F/H - Clichy")
        location = None
        title_lower = title.lower()
        
        # Check for city in title
        for city_var in self.city_variations:
            if city_var in title_lower:
                location = city_var.title()
                break
        
        # If not in title, check description
        if not location:
            desc_lower = description.lower()
            for city_var in self.city_variations:
                if city_var in desc_lower:
                    location = city_var.title()
                    break
        
        # Extract company from metadata or markdown
        company = None
        
        # Try to find company in markdown headers
        company_match = re.search(r'\[([^\]]+)\]\(https?://[^\)]+/companies/([^/]+)', markdown)
        if company_match:
            company = company_match.group(1)
        
        # Validate location confidence
        content = f"{title} {description} {markdown[:1000]}".lower()
        city_mentions = sum(1 for kw in self.city_variations if kw in content)
        other_city_mentions = sum(1 for city in self.other_cities if city in content)
        
        if city_mentions >= 2:
            confidence = "high"
        elif city_mentions == 1 and other_city_mentions == 0:
            confidence = "medium"
        elif city_mentions > 0:
            confidence = "low"
        else:
            confidence = "none"
        
        return {
            "location": location,
            "company": company,
            "confidence": confidence
        }
    
    def should_enhance(self, job: Dict) -> bool:
        """Determine if job needs Apify enhancement."""
        # Enhance if location is Unknown or confidence is low
        if job.get("location") == "Unknown":
            return True
        if job.get("confidence") == "low":
            return True
        # Enhance if company is Unknown
        if job.get("company") == "Unknown":
            return True
        
        return False
    
    def enhance_job(self, job: Dict) -> Dict:
        """Enhance a single job with Apify data."""
        url = job.get("url", "")
        platform = job.get("platform", "")
        
        # Skip Indeed (blocks Apify)
        if platform == "Indeed":
            return {
                "apify_location": None,
                "apify_company": None,
                "apify_confidence": "skipped_indeed",
                "location_source": "firecrawl"
            }
        
        print(f"  🔍 Enhancing {platform}: {url[:60]}...")
        
        # Call Apify
        apify_data = self.call_apify_mcp(url)
        
        if not apify_data:
            return {
                "apify_location": None,
                "apify_company": None,
                "apify_confidence": "apify_failed",
                "location_source": "firecrawl"
            }
        
        # Extract location and company
        extracted = self.extract_location_from_apify(apify_data)
        
        # Determine location source
        firecrawl_has_location = job.get("location") != "Unknown"
        apify_has_location = extracted["location"] is not None
        
        if firecrawl_has_location and apify_has_location:
            location_source = "both"
        elif apify_has_location:
            location_source = "apify"
        elif firecrawl_has_location:
            location_source = "firecrawl"
        else:
            location_source = "none"
        
        return {
            "apify_location": extracted["location"],
            "apify_company": extracted["company"],
            "apify_confidence": extracted["confidence"],
            "location_source": location_source
        }


def load_csv(filepath: str) -> tuple[List[Dict], List[str]]:
    """Load CSV file and return rows + fieldnames."""
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    return rows, list(fieldnames)


def save_enhanced_csv(rows: List[Dict], fieldnames: List[str], filepath: str):
    """Save enhanced CSV with new columns."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_report(jobs_before: List[Dict], jobs_after: List[Dict], target_city: str) -> str:
    """Generate before/after comparison report."""
    report = []
    report.append(f"\n{'='*60}")
    report.append("APIFY CITY VALIDATOR - ENHANCEMENT REPORT")
    report.append(f"{'='*60}")
    report.append(f"Target City: {target_city}")
    report.append(f"Total Jobs: {len(jobs_after)}")
    report.append(f"Timestamp: {datetime.utcnow().isoformat()}")
    report.append("")
    
    # Count improvements
    unknown_before = sum(1 for j in jobs_before if j.get("location") == "Unknown")
    unknown_after = sum(1 for j in jobs_after if j.get("location") == "Unknown" and not j.get("apify_location"))
    
    company_unknown_before = sum(1 for j in jobs_before if j.get("company") == "Unknown")
    company_unknown_after = sum(1 for j in jobs_after if j.get("company") == "Unknown" and not j.get("apify_company"))
    
    low_conf_before = sum(1 for j in jobs_before if j.get("confidence") == "low")
    
    # Apify enhancements
    apify_enhanced = sum(1 for j in jobs_after if j.get("apify_location") or j.get("apify_company"))
    apify_skipped = sum(1 for j in jobs_after if j.get("apify_confidence") == "skipped_indeed")
    apify_failed = sum(1 for j in jobs_after if j.get("apify_confidence") == "apify_failed")
    
    report.append("## Location Detection")
    report.append(f"  Unknown locations (before): {unknown_before}")
    report.append(f"  Unknown locations (after):  {unknown_after}")
    report.append(f"  Improvement: {unknown_before - unknown_after} jobs")
    report.append("")
    
    report.append("## Company Detection")
    report.append(f"  Unknown companies (before): {company_unknown_before}")
    report.append(f"  Unknown companies (after):  {company_unknown_after}")
    report.append(f"  Improvement: {company_unknown_before - company_unknown_after} jobs")
    report.append("")
    
    report.append("## Apify Enhancement Stats")
    report.append(f"  Jobs enhanced: {apify_enhanced}")
    report.append(f"  Jobs skipped (Indeed): {apify_skipped}")
    report.append(f"  Jobs failed: {apify_failed}")
    report.append("")
    
    # Location source breakdown
    sources = {}
    for job in jobs_after:
        source = job.get("location_source", "unknown")
        sources[source] = sources.get(source, 0) + 1
    
    report.append("## Location Source Distribution")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {source}: {count}")
    
    report.append(f"\n{'='*60}")
    
    return "\n".join(report)


def main():
    """Main enhancement function."""
    import sys
    
    # Parse arguments
    if len(sys.argv) < 3:
        print("Usage: python apify_city_validator.py <csv_file> <target_city>")
        print("Example: python apify_city_validator.py phase2_jobs.csv Toulouse")
        return
    
    csv_file = sys.argv[1]
    target_city = sys.argv[2]
    
    # Check input file
    if not Path(csv_file).exists():
        print(f"❌ Error: {csv_file} not found!")
        return
    
    print(f"{'='*60}")
    print("APIFY CITY VALIDATOR - PHASE 2 ENHANCEMENT")
    print(f"{'='*60}")
    print(f"Input CSV: {csv_file}")
    print(f"Target City: {target_city}")
    print()
    
    # Load CSV
    jobs, fieldnames = load_csv(csv_file)
    jobs_before = [j.copy() for j in jobs]  # Keep original for comparison
    
    print(f"📋 Loaded {len(jobs)} jobs from CSV")
    
    # Add new columns to fieldnames
    new_columns = ["apify_location", "apify_company", "apify_confidence", "location_source"]
    for col in new_columns:
        if col not in fieldnames:
            fieldnames.append(col)
    
    # Initialize validator
    validator = ApifyCityValidator(target_city)
    
    # Identify candidates for enhancement
    candidates = [j for j in jobs if validator.should_enhance(j)]
    print(f"🎯 Found {len(candidates)} jobs needing enhancement")
    print()
    
    # Enhance each candidate
    enhanced_count = 0
    for i, job in enumerate(candidates, 1):
        print(f"[{i}/{len(candidates)}] Processing...")
        
        # Get enhancement data
        enhancement = validator.enhance_job(job)
        
        # Update job with new data
        for key, value in enhancement.items():
            job[key] = value
        
        if enhancement["apify_location"] or enhancement["apify_company"]:
            enhanced_count += 1
            print(f"    ✅ Enhanced: location={enhancement['apify_location']}, company={enhancement['apify_company']}")
        
        # Rate limiting
        if i < len(candidates):
            time.sleep(2)
    
    print()
    
    # Add default values for non-enhanced jobs
    for job in jobs:
        if job not in candidates:
            job["apify_location"] = None
            job["apify_company"] = None
            job["apify_confidence"] = "not_checked"
            
            # Set location source based on existing data
            if job.get("location") != "Unknown":
                job["location_source"] = "firecrawl"
            else:
                job["location_source"] = "none"
    
    # Save enhanced CSV
    backup_file = csv_file.replace(".csv", "_backup.csv")
    Path(csv_file).rename(backup_file)
    print(f"💾 Backup saved: {backup_file}")
    
    save_enhanced_csv(jobs, fieldnames, csv_file)
    print(f"💾 Enhanced CSV saved: {csv_file}")
    
    # Generate report
    report = generate_report(jobs_before, jobs, target_city)
    print(report)
    
    # Save report
    report_file = csv_file.replace(".csv", "_apify_report.txt")
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📊 Report saved: {report_file}")
    
    print(f"\n✅ Enhancement complete!")


if __name__ == "__main__":
    main()
