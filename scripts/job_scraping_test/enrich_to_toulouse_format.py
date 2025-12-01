#!/usr/bin/env python3
"""
Enrich phase2_jobs.csv to match toulouse_findall_results°°.csv format

Takes the current phase2_jobs.csv with Apify enhancement data and transforms it to:
- Job Title: Use apify_title if available, otherwise title
- Company: Use apify_company if available, otherwise company or extract from description
- Location: Use apify_location if available, otherwise location
- URL: Keep as-is
- Role Type: Extract from title (Product Manager, Product Owner, PM, etc.)
- Source: Map platform to readable name (WTTJ -> "Welcome to the Jungle", etc.)
- Description: Keep first 200-300 chars as summary
- Match Status: "Matched" for all (they already passed initial filtering)
"""

import csv
import re
import os
from pathlib import Path

# Script configuration
INPUT_CSV = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/phase2_jobs.csv")
OUTPUT_CSV = Path("/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/job_scraping_test/phase2_jobs_enriched.csv")

# Platform name mapping
PLATFORM_MAP = {
    "WTTJ": "Welcome to the Jungle",
    "LinkedIn": "LinkedIn", 
    "Indeed": "Indeed",
    "Glassdoor": "Glassdoor"
}

def clean_text(text):
    """Clean text by removing extra whitespace and special chars"""
    if not text or text == "Unknown":
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove excessive whitespace
    text = ' '.join(text.split())
    # Remove quotes
    text = text.replace('"', '').replace("'", "")
    return text.strip()

def extract_company_from_description(description):
    """Try to extract company name from description markdown"""
    if not description:
        return "N/A"
    
    # Look for markdown link pattern: [Company](url)
    match = re.search(r'\[([^\]]+)\]\(https://www\.welcometothejungle\.com/[^\)]+/companies/([^\)]+)\)', description)
    if match:
        return match.group(1)
    
    # Look for company after ## heading
    match = re.search(r'##\s+(.+?)(?:\n|$)', description)
    if match and not match.group(1).startswith('Product'):
        company_line = match.group(1).strip()
        # Remove job title if it's in the same line
        if ' - ' in company_line:
            parts = company_line.split(' - ')
            return parts[-1] if len(parts) > 1 else parts[0]
        return company_line
    
    return "N/A"

def extract_role_types(title):
    """Extract role types from job title"""
    if not title or title == "Unknown":
        return "Product Manager"
    
    roles = []
    title_lower = title.lower()
    
    # Check for specific roles
    if "product owner" in title_lower or "po" in title_lower:
        roles.append("Product Owner")
    if "product manager" in title_lower or "pm" in title_lower:
        roles.append("Product Manager")
    if "product marketing" in title_lower:
        roles.append("Product Marketing Manager")
    if "senior" in title_lower:
        roles.append("Senior Product Manager")
    if "lead" in title_lower or "head" in title_lower:
        roles.append("Lead Product Manager")
    if "director" in title_lower or "executive" in title_lower:
        roles.append("Executive Director")
    if "chef de projet" in title_lower or "proxy" in title_lower:
        roles.append("Project Lead")
    
    # If no specific roles found, default
    if not roles:
        roles = ["Product Manager"]
    
    return ", ".join(roles)

def get_best_location(row):
    """Get best available location from multiple sources"""
    # Priority: apify_location > location > extract from description
    if row.get('apify_location') and row['apify_location'] not in ['Unknown', '', 'N/A']:
        return row['apify_location']
    
    if row.get('location') and row['location'] not in ['Unknown', '', 'N/A']:
        # Clean up location formatting
        location = row['location']
        if '**' in location:
            location = location.replace('**', '').strip()
        if 'france' in location.lower():
            # Extract city before ", france"
            match = re.search(r'([^,]+),?\s*france', location, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        return location
    
    # Try to extract from description
    desc = row.get('description', '')
    # Look for location patterns
    patterns = [
        r'##[^\n]*\n[^\n]*\n([A-Z][a-zé\-]+)(?:\s|$)',  # After markdown title
        r'CDI\s+([A-Z][a-zé\-]+)',  # After CDI
        r'Télétravail\s+[^\n]*\n[^\n]*\n([A-Z][a-zé\-]+)'  # After Télétravail
    ]
    
    for pattern in patterns:
        match = re.search(pattern, desc)
        if match:
            location = match.group(1)
            if location not in ['Non', 'Résumé', 'Salaire', 'Expérience', 'Éducation', 'Compétences']:
                return location
    
    return "Unknown"

def get_best_company(row):
    """Get best available company name from multiple sources"""
    # Priority: apify_company > company > extract from description
    if row.get('apify_company') and row['apify_company'] not in ['Unknown', '', 'N/A', 'Groupe ADENES']:
        return row['apify_company']
    
    if row.get('company') and row['company'] not in ['Unknown', '', 'N/A']:
        return row['company']
    
    # Try to extract from description
    company = extract_company_from_description(row.get('description', ''))
    return company if company != "N/A" else "N/A"

def get_best_title(row):
    """Get best available title from multiple sources"""
    # Priority: apify_title > title > extract from description
    if row.get('apify_title') and row['apify_title'] not in ['Unknown', '', 'N/A']:
        title = row['apify_title']
        # Clean up long titles
        if ' - ' in title and len(title) > 100:
            # Keep only the job title part (before company/location)
            parts = title.split(' - ')
            return parts[0]
        return title
    
    if row.get('title') and row['title'] not in ['Unknown', '', 'N/A']:
        return row['title']
    
    # Try to extract from description
    desc = row.get('description', '')
    match = re.search(r'##\s+(.+?)(?:\n|$)', desc)
    if match:
        return match.group(1).strip()
    
    return "Product Manager (Title Unknown)"

def create_description_summary(row):
    """Create a concise description summary"""
    desc = row.get('description', '')
    if not desc or desc == 'Unknown':
        return f"A {row.get('platform', 'job board')} listing for a product management role."
    
    # Clean HTML and markdown
    desc = clean_text(desc)
    
    # Remove URLs
    desc = re.sub(r'https?://\S+', '', desc)
    
    # Take first 250 characters
    if len(desc) > 250:
        desc = desc[:247] + "..."
    
    return desc if desc else "Product management position."

def enrich_csv():
    """Main enrichment function"""
    print(f"📖 Reading input CSV: {INPUT_CSV}")
    
    if not INPUT_CSV.exists():
        print(f"❌ ERROR: Input file not found: {INPUT_CSV}")
        return
    
    enriched_rows = []
    stats = {
        'total': 0,
        'apify_title': 0,
        'apify_company': 0, 
        'apify_location': 0,
        'by_platform': {}
    }
    
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            stats['total'] += 1
            platform = row.get('platform', 'Unknown')
            stats['by_platform'][platform] = stats['by_platform'].get(platform, 0) + 1
            
            # Track Apify enhancements
            if row.get('apify_title'):
                stats['apify_title'] += 1
            if row.get('apify_company'):
                stats['apify_company'] += 1
            if row.get('apify_location'):
                stats['apify_location'] += 1
            
            # Build enriched row
            title = get_best_title(row)
            company = get_best_company(row)
            location = get_best_location(row)
            
            enriched_row = {
                'Job Title': title,
                'Company': company,
                'Location': location,
                'URL': row.get('url', ''),
                'Role Type': extract_role_types(title),
                'Source': PLATFORM_MAP.get(platform, platform),
                'Description': create_description_summary(row),
                'Match Status': 'Matched'
            }
            
            enriched_rows.append(enriched_row)
    
    # Write enriched CSV
    print(f"\n✍️  Writing enriched CSV: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Job Title', 'Company', 'Location', 'URL', 'Role Type', 'Source', 'Description', 'Match Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in enriched_rows:
            writer.writerow(row)
    
    # Print statistics
    print(f"\n📊 ENRICHMENT STATISTICS")
    print(f"=" * 50)
    print(f"Total jobs processed: {stats['total']}")
    print(f"\nApify Enhancements:")
    print(f"  - Titles: {stats['apify_title']} ({stats['apify_title']/stats['total']*100:.1f}%)")
    print(f"  - Companies: {stats['apify_company']} ({stats['apify_company']/stats['total']*100:.1f}%)")
    print(f"  - Locations: {stats['apify_location']} ({stats['apify_location']/stats['total']*100:.1f}%)")
    
    print(f"\nBy Platform:")
    for platform, count in sorted(stats['by_platform'].items()):
        print(f"  - {PLATFORM_MAP.get(platform, platform)}: {count}")
    
    print(f"\n✅ Enrichment complete!")
    print(f"📄 Output: {OUTPUT_CSV}")

if __name__ == "__main__":
    enrich_csv()
