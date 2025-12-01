#!/usr/bin/env python3
"""
Enhance phase2_jobs_enriched.csv with Apify data

This script takes the enriched CSV (toulouse_findall format) and attempts to:
1. Extract better title/company/location data from URLs using Apify
2. Update the CSV with enhanced data
3. Generate a report of improvements

Supports: WTTJ, Glassdoor (with 403 handling), LinkedIn (skip), Indeed (skip)
"""

import csv
import time
import json
import os
from pathlib import Path
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
INPUT_CSV = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/phase2_jobs_enriched.csv")
OUTPUT_CSV = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/phase2_jobs_enriched_apify.csv")
REPORT_FILE = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/apify_enriched_report.txt")
LOG_FILE = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/apify_enriched_log.json")

# Apify configuration
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
ACTOR_ID = "apify/rag-web-browser"
RATE_LIMIT_DELAY = 2  # seconds between requests

class ApifyEnricher:
    def __init__(self):
        self.client = ApifyClient(APIFY_API_KEY)
        self.actor = self.client.actor(ACTOR_ID)
        self.stats = {
            'total': 0,
            'processed': 0,
            'enhanced': 0,
            'skipped': 0,
            'errors': 0,
            'by_source': {}
        }
        self.log_entries = []
    
    def extract_from_metadata(self, items):
        """Extract title, company, location from Apify response"""
        if not items or len(items) == 0:
            return None, None, None, "low"
        
        item = items[0]
        metadata = item.get('metadata', {})
        
        # Extract from metadata.title (WTTJ pattern: "Job Title - Company - CDI à City")
        title_text = metadata.get('title', '')
        
        title = None
        company = None
        location = None
        confidence = "low"
        
        if title_text and ' - ' in title_text and ' à ' in title_text:
            # WTTJ pattern detected
            parts = title_text.split(' - ')
            if len(parts) >= 2:
                title = parts[0].strip()
                
                # Check if last part has location
                last_part = parts[-1]
                if ' à ' in last_part:
                    # Extract company (everything between title and location)
                    company_parts = parts[1:-1]
                    if company_parts:
                        company = ' - '.join(company_parts).strip()
                    else:
                        # Company might be in the location part before "à"
                        location_split = last_part.split(' à ')
                        if len(location_split) == 2:
                            company = location_split[0].replace('CDI', '').strip()
                            location = location_split[1].strip()
                    
                    # Extract location
                    if ' à ' in last_part:
                        location = last_part.split(' à ')[-1].strip()
                
                confidence = "high"
        
        # Fallback: try to extract from description
        if not location or not company:
            text = item.get('text', '')
            markdown = item.get('markdown', '')
            
            # Try to find location in text
            if not location:
                for city_keyword in ['Paris', 'Lyon', 'Toulouse', 'Marseille', 'Bordeaux', 
                                     'Lille', 'Nantes', 'Strasbourg', 'Montpellier', 'Nice',
                                     'Clichy', 'Pantin', 'Marcoussis', 'Gennevilliers', 'Beauvais']:
                    if city_keyword.lower() in text.lower():
                        location = city_keyword
                        break
            
            # Try to find company in markdown
            if not company and markdown:
                # Look for company links
                import re
                company_match = re.search(r'\[([^\]]+)\]\(https://www\.welcometothejungle\.com/[^\)]+/companies/', markdown)
                if company_match:
                    company = company_match.group(1)
        
        # Filter out false positives
        if location and location.lower() in ['cdi', 'remote', 'france', 'télétravail', 'hybrid']:
            location = None
        
        if company and len(company) > 100:  # Too long, probably not a company name
            company = None
        
        return title, company, location, confidence
    
    def call_apify_actor(self, url):
        """Call Apify Actor for a single URL"""
        try:
            run_input = {
                "query": url,
                "maxResults": 1,
                "outputFormats": ["markdown"]
            }
            
            print(f"  📞 Calling Apify Actor for URL...")
            run = self.actor.call(run_input=run_input)
            
            # Get results
            dataset = self.client.dataset(run['defaultDatasetId'])
            items = dataset.list_items().items
            
            return items, run['id']
            
        except Exception as e:
            raise Exception(f"Actor call failed: {str(e)}")
    
    def should_process_job(self, row):
        """Determine if job should be processed"""
        source = row.get('Source', '')
        url = row.get('URL', '')
        title = row.get('Job Title', '')
        company = row.get('Company', '')
        location = row.get('Location', '')
        
        # Skip if already has complete data
        if (title and title not in ['Product Manager (Title Unknown)', 'Unknown', '', 'N/A'] and
            company and company not in ['Unknown', '', 'N/A'] and
            location and location not in ['Unknown', '', 'N/A']):
            return False, "already_complete"
        
        # Skip LinkedIn (encrypted)
        if 'LinkedIn' in source or 'linkedin.com' in url:
            return False, "linkedin_encrypted"
        
        # Skip Indeed (403 blocks + already has good data)
        if 'Indeed' in source or 'indeed.com' in url or 'indeed.fr' in url:
            return False, "indeed_blocked"
        
        # Process WTTJ
        if 'Welcome to the Jungle' in source or 'welcometothejungle.com' in url:
            return True, "wttj_processable"
        
        # Process Glassdoor (will likely 403, but try)
        if 'Glassdoor' in source or 'glassdoor' in url:
            return True, "glassdoor_attempt"
        
        return False, "unknown_source"
    
    def enhance_csv(self):
        """Main enhancement function"""
        print(f"📖 Reading enriched CSV: {INPUT_CSV}\n")
        
        if not INPUT_CSV.exists():
            print(f"❌ ERROR: Input file not found: {INPUT_CSV}")
            return
        
        enhanced_rows = []
        
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for idx, row in enumerate(reader, start=1):
                self.stats['total'] += 1
                source = row.get('Source', 'Unknown')
                self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
                
                print(f"\n[{idx}/{self.stats['total']}] Processing: {row.get('Job Title', 'Unknown')[:50]}...")
                print(f"  📍 Source: {source}")
                print(f"  📍 Current: {row.get('Company', 'N/A')}, {row.get('Location', 'Unknown')}")
                
                # Check if should process
                should_process, reason = self.should_process_job(row)
                
                if not should_process:
                    print(f"  ⏭️  Skipped: {reason}")
                    self.stats['skipped'] += 1
                    self.log_entries.append({
                        'row': idx,
                        'title': row.get('Job Title', ''),
                        'source': source,
                        'action': 'skipped',
                        'reason': reason,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Add empty enhancement columns
                    row['Apify Title'] = ''
                    row['Apify Company'] = ''
                    row['Apify Location'] = ''
                    row['Apify Confidence'] = ''
                    row['Apify Run ID'] = ''
                    enhanced_rows.append(row)
                    continue
                
                # Process with Apify
                self.stats['processed'] += 1
                url = row.get('URL', '')
                
                try:
                    items, run_id = self.call_apify_actor(url)
                    title, company, location, confidence = self.extract_from_metadata(items)
                    
                    if title or company or location:
                        print(f"  ✅ Enhanced: {title or 'N/A'}, {company or 'N/A'}, {location or 'N/A'} (confidence: {confidence})")
                        self.stats['enhanced'] += 1
                        
                        # Update row with enhancements
                        row['Apify Title'] = title or ''
                        row['Apify Company'] = company or ''
                        row['Apify Location'] = location or ''
                        row['Apify Confidence'] = confidence
                        row['Apify Run ID'] = run_id
                        
                        # Update main columns if better data available
                        if title and row.get('Job Title') in ['Product Manager (Title Unknown)', 'Unknown', '']:
                            row['Job Title'] = title
                        if company and row.get('Company') in ['N/A', 'Unknown', '']:
                            row['Company'] = company
                        if location and row.get('Location') in ['Unknown', '']:
                            row['Location'] = location
                        
                        self.log_entries.append({
                            'row': idx,
                            'title': row.get('Job Title', ''),
                            'source': source,
                            'action': 'enhanced',
                            'apify_title': title,
                            'apify_company': company,
                            'apify_location': location,
                            'confidence': confidence,
                            'run_id': run_id,
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        print(f"  ⚠️  No data extracted")
                        self.stats['errors'] += 1
                        row['Apify Title'] = ''
                        row['Apify Company'] = ''
                        row['Apify Location'] = ''
                        row['Apify Confidence'] = 'none'
                        row['Apify Run ID'] = run_id
                        
                        self.log_entries.append({
                            'row': idx,
                            'title': row.get('Job Title', ''),
                            'source': source,
                            'action': 'failed',
                            'reason': 'no_data_extracted',
                            'run_id': run_id,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    enhanced_rows.append(row)
                    time.sleep(RATE_LIMIT_DELAY)
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ❌ Error: {error_msg[:100]}")
                    self.stats['errors'] += 1
                    
                    row['Apify Title'] = ''
                    row['Apify Company'] = ''
                    row['Apify Location'] = ''
                    row['Apify Confidence'] = 'error'
                    row['Apify Run ID'] = ''
                    
                    self.log_entries.append({
                        'row': idx,
                        'title': row.get('Job Title', ''),
                        'source': source,
                        'action': 'error',
                        'error': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    enhanced_rows.append(row)
                    time.sleep(RATE_LIMIT_DELAY)
        
        # Write enhanced CSV
        print(f"\n\n✍️  Writing enhanced CSV: {OUTPUT_CSV}")
        
        fieldnames = list(enhanced_rows[0].keys())
        with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in enhanced_rows:
                writer.writerow(row)
        
        # Generate report
        self.generate_report()
        
        # Save log
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.log_entries, f, indent=2)
        
        print(f"\n📄 Report: {REPORT_FILE}")
        print(f"📄 Log: {LOG_FILE}")
    
    def generate_report(self):
        """Generate enhancement report"""
        report_lines = [
            "=" * 60,
            "APIFY ENRICHED CSV ENHANCEMENT REPORT",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 60,
            f"Total jobs: {self.stats['total']}",
            f"Processed: {self.stats['processed']}",
            f"Enhanced: {self.stats['enhanced']}",
            f"Skipped: {self.stats['skipped']}",
            f"Errors: {self.stats['errors']}",
            "",
            f"Enhancement Rate: {self.stats['enhanced']/self.stats['processed']*100:.1f}% ({self.stats['enhanced']}/{self.stats['processed']})" if self.stats['processed'] > 0 else "Enhancement Rate: 0%",
            "",
            "BY SOURCE",
            "-" * 60,
        ]
        
        for source, count in sorted(self.stats['by_source'].items()):
            report_lines.append(f"{source}: {count} jobs")
        
        report_lines.extend([
            "",
            "DETAILED RESULTS",
            "-" * 60,
        ])
        
        # Group results
        enhanced = [e for e in self.log_entries if e['action'] == 'enhanced']
        skipped = [e for e in self.log_entries if e['action'] == 'skipped']
        errors = [e for e in self.log_entries if e['action'] in ['error', 'failed']]
        
        if enhanced:
            report_lines.append(f"\n✅ ENHANCED ({len(enhanced)} jobs):")
            for entry in enhanced:
                report_lines.append(f"  Row {entry['row']}: {entry['title'][:50]}")
                report_lines.append(f"    → {entry['apify_company'] or 'N/A'}, {entry['apify_location'] or 'N/A'}")
        
        if errors:
            report_lines.append(f"\n❌ ERRORS ({len(errors)} jobs):")
            for entry in errors[:10]:  # Show first 10
                report_lines.append(f"  Row {entry['row']}: {entry['title'][:50]}")
                report_lines.append(f"    Reason: {entry.get('reason', entry.get('error', 'Unknown'))[:80]}")
        
        if skipped:
            report_lines.append(f"\n⏭️  SKIPPED ({len(skipped)} jobs):")
            skip_reasons = {}
            for entry in skipped:
                reason = entry['reason']
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            for reason, count in sorted(skip_reasons.items()):
                report_lines.append(f"  {reason}: {count} jobs")
        
        report_lines.extend([
            "",
            "=" * 60,
            "END OF REPORT",
            "=" * 60
        ])
        
        report_text = '\n'.join(report_lines)
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print("\n" + report_text)

if __name__ == "__main__":
    enricher = ApifyEnricher()
    enricher.enhance_csv()
    print("\n✅ Enhancement complete!")
