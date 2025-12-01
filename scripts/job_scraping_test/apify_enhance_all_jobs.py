#!/usr/bin/env python3
"""
Apify Job Enhancement Script - Full Dataset Processor
Processes all jobs in phase2_jobs.csv and enhances data using Apify API.

Usage:
    python apify_enhance_all_jobs.py

Features:
- Processes WTTJ, Glassdoor, LinkedIn, and Indeed URLs
- Extracts location (city), company name, job title
- Handles platform-specific extraction patterns
- Updates CSV with enhanced data columns
- Generates comprehensive comparison report
- Rate limiting and error handling

Output:
- Updated phase2_jobs.csv with new columns
- apify_enhancement_report.txt with before/after stats
- apify_enhancement_log.json with detailed processing logs
"""

import os
import csv
import json
import time
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/.env")


# Configuration
CSV_FILE = "/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/phase2_jobs.csv"
REPORT_FILE = "/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/apify_enhancement_report.txt"
LOG_FILE = "/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/apify_enhancement_log.json"
ACTOR_ID = "apify/rag-web-browser"
REQUEST_DELAY = 2  # seconds between Apify calls


class ApifyJobEnhancer:
    """Enhances job data using Apify RAG Web Browser Actor"""
    
    def __init__(self):
        """Initialize Apify client and load environment"""
        api_key = os.getenv('APIFY_API_KEY')
        if not api_key:
            raise ValueError("APIFY_API_KEY not found in environment")
        
        self.client = ApifyClient(api_key)
        self.actor = self.client.actor(ACTOR_ID)
        self.processing_log = []
        self.stats = {
            'total_jobs': 0,
            'processed': 0,
            'enhanced': 0,
            'skipped': 0,
            'errors': 0,
            'by_platform': {}
        }
    
    def extract_from_metadata(self, items: List[Dict]) -> Dict[str, Optional[str]]:
        """
        Extract job data from Apify metadata.
        
        Handles different patterns:
        - WTTJ: "Job Title - Company - CDI à City"
        - Glassdoor: Various title formats
        - LinkedIn: Title with location in description
        - Indeed: Mixed formats
        """
        if not items or len(items) == 0:
            return {'title': None, 'company': None, 'location': None}
        
        item = items[0]
        metadata = item.get('metadata', {})
        title = metadata.get('title', '')
        description = metadata.get('description', '')
        
        result = {
            'title': None,
            'company': None,
            'location': None
        }
        
        # Extract location from title (WTTJ pattern: "... à City")
        if ' à ' in title:
            parts = title.split(' à ')
            city = parts[-1].strip()
            result['location'] = city
            
            # Try to extract title and company from first part
            first_part = parts[0]
            if ' - ' in first_part:
                sub_parts = first_part.split(' - ')
                if len(sub_parts) >= 2:
                    result['title'] = sub_parts[0].strip()
                    result['company'] = sub_parts[1].strip()
                elif len(sub_parts) == 1:
                    result['title'] = sub_parts[0].strip()
            else:
                result['title'] = first_part.strip()
        
        # Extract from description if title is empty
        if not result['title'] and title:
            result['title'] = title.strip()
        
        # Try to extract company from description
        if not result['company'] and description:
            # Look for company patterns
            company_patterns = [
                r'(?:chez|at|pour|with)\s+([A-Z][A-Za-z\s&\'-]+)',
                r'([A-Z][A-Za-z\s&\'-]+)\s+(?:recherche|recrute|is hiring)',
            ]
            for pattern in company_patterns:
                match = re.search(pattern, description)
                if match:
                    result['company'] = match.group(1).strip()
                    break
        
        # Try to extract location from description if not found
        if not result['location']:
            # French cities pattern
            location_patterns = [
                r'\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b',  # City name
                r'(?:basé[e]? à|located in|in)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)',
            ]
            for pattern in location_patterns:
                match = re.search(pattern, description)
                if match:
                    candidate = match.group(1).strip()
                    # Filter out common false positives
                    if candidate not in ['CDI', 'Remote', 'France', 'Europe']:
                        result['location'] = candidate
                        break
        
        return result
    
    def call_apify_actor(self, url: str, platform: str) -> Optional[Dict]:
        """
        Call Apify Actor for a single URL.
        
        Returns extracted data or None if failed.
        """
        try:
            print(f"  🔍 Processing {platform}: {url[:60]}...")
            
            # Call Actor
            run = self.actor.call(run_input={
                "query": url,
                "maxResults": 1,
                "outputFormats": ["markdown"]
            })
            
            if not run or run.get('status') != 'SUCCEEDED':
                print(f"    ❌ Actor run failed: {run.get('status', 'UNKNOWN')}")
                return None
            
            # Get results from dataset
            dataset_id = run.get('defaultDatasetId')
            if not dataset_id:
                print(f"    ❌ No dataset ID returned")
                return None
            
            dataset = self.client.dataset(dataset_id)
            items = dataset.list_items().items
            
            if not items:
                print(f"    ❌ No items in dataset")
                return None
            
            # Extract data
            extracted = self.extract_from_metadata(items)
            
            # Log success
            if any(extracted.values()):
                print(f"    ✅ Extracted: {extracted}")
                return {
                    'url': url,
                    'platform': platform,
                    'extracted': extracted,
                    'actor_run_id': run.get('id'),
                    'success': True
                }
            else:
                print(f"    ⚠️ No data extracted")
                return None
        
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            return None
    
    def should_process_job(self, job: Dict) -> Tuple[bool, str]:
        """
        Determine if job should be processed based on platform and existing data.
        
        Returns (should_process, reason)
        """
        platform = job.get('platform', '').upper()
        location = job.get('location', 'Unknown')
        company = job.get('company', 'Unknown')
        
        # Skip if already enhanced by Apify
        if job.get('location_source') == 'apify':
            return False, "already_apified"
        
        # Skip Indeed (403 blocks from Apify, but has good data)
        if platform == 'INDEED':
            return False, "indeed_blocked"
        
        # Skip LinkedIn (encrypted/dynamic content)
        if platform == 'LINKEDIN':
            return False, "linkedin_encrypted"
        
        # Process WTTJ (100% success rate)
        if platform == 'WTTJ':
            if location == 'Unknown' or company == 'Unknown':
                return True, "wttj_missing_data"
            return False, "wttj_complete"
        
        # Process Glassdoor (needs enhancement)
        if platform == 'GLASSDOOR':
            if location == 'Unknown' or company == 'Unknown':
                return True, "glassdoor_missing_data"
            return False, "glassdoor_complete"
        
        return False, "unknown_platform"
    
    def enhance_csv(self) -> Dict:
        """
        Process all jobs in CSV and enhance with Apify data.
        
        Returns processing statistics.
        """
        print(f"\n🚀 Starting Apify enhancement for {CSV_FILE}")
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Read existing CSV
        jobs = []
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            jobs = list(reader)
        
        self.stats['total_jobs'] = len(jobs)
        
        # Ensure new columns exist
        new_columns = ['apify_title', 'apify_company', 'apify_location', 'apify_confidence', 'apify_run_id']
        for col in new_columns:
            if col not in fieldnames:
                fieldnames = list(fieldnames) + [col]
        
        # Process each job
        for idx, job in enumerate(jobs, 1):
            url = job.get('url', '')
            platform = job.get('platform', 'UNKNOWN')
            
            print(f"\n[{idx}/{len(jobs)}] {platform} - {url[:60]}...")
            
            # Check if should process
            should_process, reason = self.should_process_job(job)
            
            if not should_process:
                print(f"  ⏭️  Skipped: {reason}")
                self.stats['skipped'] += 1
                self.processing_log.append({
                    'row': idx,
                    'url': url,
                    'platform': platform,
                    'action': 'skipped',
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                continue
            
            # Track by platform
            if platform not in self.stats['by_platform']:
                self.stats['by_platform'][platform] = {'processed': 0, 'enhanced': 0, 'errors': 0}
            
            # Call Apify
            result = self.call_apify_actor(url, platform)
            self.stats['processed'] += 1
            self.stats['by_platform'][platform]['processed'] += 1
            
            if result and result.get('success'):
                # Extract data
                extracted = result['extracted']
                
                # Update job with extracted data
                if extracted.get('title'):
                    job['apify_title'] = extracted['title']
                if extracted.get('company'):
                    job['apify_company'] = extracted['company']
                if extracted.get('location'):
                    job['apify_location'] = extracted['location']
                
                # Set confidence
                confidence_count = sum(1 for v in extracted.values() if v)
                if confidence_count >= 3:
                    job['apify_confidence'] = 'high'
                elif confidence_count >= 2:
                    job['apify_confidence'] = 'medium'
                else:
                    job['apify_confidence'] = 'low'
                
                job['apify_run_id'] = result.get('actor_run_id', '')
                
                # Update location_source if location was found
                if extracted.get('location'):
                    if job.get('location') == 'Unknown':
                        job['location_source'] = 'apify'
                    else:
                        job['location_source'] = 'both'
                
                self.stats['enhanced'] += 1
                self.stats['by_platform'][platform]['enhanced'] += 1
                
                self.processing_log.append({
                    'row': idx,
                    'url': url,
                    'platform': platform,
                    'action': 'enhanced',
                    'extracted': extracted,
                    'run_id': result.get('actor_run_id'),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.stats['errors'] += 1
                self.stats['by_platform'][platform]['errors'] += 1
                
                self.processing_log.append({
                    'row': idx,
                    'url': url,
                    'platform': platform,
                    'action': 'error',
                    'reason': 'apify_call_failed',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Rate limiting
            if idx < len(jobs):
                print(f"  ⏳ Waiting {REQUEST_DELAY}s...")
                time.sleep(REQUEST_DELAY)
        
        # Write updated CSV
        print(f"\n💾 Writing updated CSV...")
        with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)
        
        print(f"✅ CSV updated: {CSV_FILE}")
        
        return self.stats
    
    def generate_report(self):
        """Generate comprehensive enhancement report"""
        print(f"\n📊 Generating enhancement report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("APIFY JOB ENHANCEMENT REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"CSV File: {CSV_FILE}")
        report_lines.append(f"Actor: {ACTOR_ID}")
        
        # Overall stats
        report_lines.append("\n" + "=" * 80)
        report_lines.append("OVERALL STATISTICS")
        report_lines.append("=" * 80)
        report_lines.append(f"Total Jobs: {self.stats['total_jobs']}")
        report_lines.append(f"Processed: {self.stats['processed']}")
        report_lines.append(f"Enhanced: {self.stats['enhanced']}")
        report_lines.append(f"Skipped: {self.stats['skipped']}")
        report_lines.append(f"Errors: {self.stats['errors']}")
        
        # Calculate percentages
        if self.stats['processed'] > 0:
            enhancement_rate = (self.stats['enhanced'] / self.stats['processed']) * 100
            report_lines.append(f"\nEnhancement Rate: {enhancement_rate:.1f}% ({self.stats['enhanced']}/{self.stats['processed']})")
        
        # By platform
        report_lines.append("\n" + "=" * 80)
        report_lines.append("BY PLATFORM")
        report_lines.append("=" * 80)
        for platform, stats in sorted(self.stats['by_platform'].items()):
            report_lines.append(f"\n{platform}:")
            report_lines.append(f"  Processed: {stats['processed']}")
            report_lines.append(f"  Enhanced: {stats['enhanced']}")
            report_lines.append(f"  Errors: {stats['errors']}")
            if stats['processed'] > 0:
                success_rate = (stats['enhanced'] / stats['processed']) * 100
                report_lines.append(f"  Success Rate: {success_rate:.1f}%")
        
        # New columns added
        report_lines.append("\n" + "=" * 80)
        report_lines.append("NEW COLUMNS ADDED")
        report_lines.append("=" * 80)
        report_lines.append("- apify_title: Job title extracted by Apify")
        report_lines.append("- apify_company: Company name extracted by Apify")
        report_lines.append("- apify_location: City/location extracted by Apify")
        report_lines.append("- apify_confidence: Extraction confidence (high/medium/low)")
        report_lines.append("- apify_run_id: Apify Actor run ID for traceability")
        
        # Processing summary
        report_lines.append("\n" + "=" * 80)
        report_lines.append("PROCESSING SUMMARY")
        report_lines.append("=" * 80)
        
        # Count by action
        actions = {}
        for log in self.processing_log:
            action = log.get('action', 'unknown')
            actions[action] = actions.get(action, 0) + 1
        
        for action, count in sorted(actions.items()):
            report_lines.append(f"{action.upper()}: {count}")
        
        # Write report
        report_content = "\n".join(report_lines)
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Report saved: {REPORT_FILE}")
        
        # Write processing log
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': self.stats,
                'processing_log': self.processing_log,
                'generated_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"✅ Log saved: {LOG_FILE}")
        
        # Print report summary
        print("\n" + report_content)


def main():
    """Main execution"""
    try:
        enhancer = ApifyJobEnhancer()
        enhancer.enhance_csv()
        enhancer.generate_report()
        
        print("\n" + "=" * 80)
        print("✅ ENHANCEMENT COMPLETE!")
        print("=" * 80)
        print(f"\nFiles updated:")
        print(f"  - CSV: {CSV_FILE}")
        print(f"  - Report: {REPORT_FILE}")
        print(f"  - Log: {LOG_FILE}")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
