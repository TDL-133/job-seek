#!/usr/bin/env python3
"""
Export enriched FindAll results to CSV with salary and company size
"""
import json
import csv

# Load enriched JSON data
try:
    with open("toulouse_enriched_results.json", "r") as f:
        data = json.load(f)
    print("✅ Loaded toulouse_enriched_results.json")
except FileNotFoundError:
    print("❌ File not found: toulouse_enriched_results.json")
    print("   Run 'python3 test_findall_with_enrichments.py' first!")
    exit(1)

matched = [c for c in data["candidates"] if c["match_status"] == "matched"]

# Create CSV
csv_file = "toulouse_enriched_results.csv"

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    
    # Header with all enrichment columns
    writer.writerow([
        "Job Title",
        "Company",
        "Location",
        "Salary Range",
        "Company Size",
        "Experience Level",
        "Industry",
        "Required Skills",
        "Contract Type",
        "Remote Policy",
        "Languages Required",
        "Benefits",
        "Posting Date",
        "URL",
        "Role Type",
        "Source",
        "Description"
    ])
    
    # Data rows
    for job in matched:
        name = job.get('name', 'N/A')
        url = job.get('url', 'N/A')
        description = job.get('description', 'N/A')
        
        output = job.get('output', {})
        role = output.get('product_manager_role_check', {}).get('value', 'N/A')
        location = output.get('toulouse_france_location_check', {}).get('value', 'N/A')
        
        # Get all 10 enrichment fields
        salary = output.get('salary_range', {}).get('value', 'Not specified')
        company_size = output.get('company_size', {}).get('value', 'Unknown')
        experience_level = output.get('experience_level', {}).get('value', 'Not specified')
        industry = output.get('industry', {}).get('value', 'Not specified')
        
        # Handle array fields (skills, languages, benefits)
        skills_data = output.get('required_skills', {}).get('value', [])
        if isinstance(skills_data, list):
            required_skills = ", ".join(skills_data) if skills_data else "Not specified"
        else:
            required_skills = skills_data if skills_data else "Not specified"
        
        contract_type = output.get('contract_type', {}).get('value', 'Not specified')
        remote_policy = output.get('remote_policy', {}).get('value', 'Not specified')
        
        languages_data = output.get('languages_required', {}).get('value', [])
        if isinstance(languages_data, list):
            languages_required = ", ".join(languages_data) if languages_data else "Not specified"
        else:
            languages_required = languages_data if languages_data else "Not specified"
        
        benefits_data = output.get('benefits', {}).get('value', [])
        if isinstance(benefits_data, list):
            benefits = ", ".join(benefits_data) if benefits_data else "Not specified"
        else:
            benefits = benefits_data if benefits_data else "Not specified"
        
        posting_date = output.get('posting_date', {}).get('value', 'Not specified')
        
        # Determine source from URL
        source = "Unknown"
        if 'glassdoor' in url.lower():
            source = "Glassdoor"
        elif 'welcometothejungle' in url.lower():
            source = "Welcome to the Jungle"
        elif 'indeed' in url.lower():
            source = "Indeed"
        elif 'linkedin' in url.lower():
            source = "LinkedIn"
        
        # Extract company from name
        company = "N/A"
        if '–' in name:
            company = name.split('–')[1].strip().split(',')[0].strip()
        elif ' at ' in name:
            company = name.split(' at ')[1].strip().split(',')[0].strip()
        
        writer.writerow([
            name,
            company,
            location,
            salary,
            company_size,
            experience_level,
            industry,
            required_skills,
            contract_type,
            remote_policy,
            languages_required,
            benefits,
            posting_date,
            url,
            role,
            source,
            description[:200]  # Limit description to 200 chars for readability
        ])

print(f"✅ Created enriched CSV file: {csv_file}")
print(f"   - {len(matched)} matched jobs exported")
print(f"   - Includes all 10 enrichment fields:")
print(f"     1. Salary Range")
print(f"     2. Company Size")
print(f"     3. Experience Level")
print(f"     4. Industry")
print(f"     5. Required Skills")
print(f"     6. Contract Type")
print(f"     7. Remote Policy")
print(f"     8. Languages Required")
print(f"     9. Benefits")
print(f"     10. Posting Date")
print()
print(f"📊 Enrichment Coverage:")
print(f"   - Salary: {sum(1 for j in matched if j.get('output', {}).get('salary_range', {}).get('value', 'Not specified') != 'Not specified')}/{len(matched)} jobs")
print(f"   - Company Size: {sum(1 for j in matched if j.get('output', {}).get('company_size', {}).get('value', 'Unknown') != 'Unknown')}/{len(matched)} jobs")
print(f"   - Experience Level: {sum(1 for j in matched if j.get('output', {}).get('experience_level', {}).get('value', 'Not specified') != 'Not specified')}/{len(matched)} jobs")
print(f"   - Industry: {sum(1 for j in matched if j.get('output', {}).get('industry', {}).get('value', 'Not specified') != 'Not specified')}/{len(matched)} jobs")
print(f"   - Skills: {sum(1 for j in matched if j.get('output', {}).get('required_skills', {}).get('value') not in [None, [], 'Not specified'])}/{len(matched)} jobs")
print(f"   - Contract Type: {sum(1 for j in matched if j.get('output', {}).get('contract_type', {}).get('value', 'Not specified') != 'Not specified')}/{len(matched)} jobs")
print(f"   - Remote Policy: {sum(1 for j in matched if j.get('output', {}).get('remote_policy', {}).get('value', 'Not specified') != 'Not specified')}/{len(matched)} jobs")
print(f"   - Languages: {sum(1 for j in matched if j.get('output', {}).get('languages_required', {}).get('value') not in [None, [], 'Not specified'])}/{len(matched)} jobs")
print(f"   - Benefits: {sum(1 for j in matched if j.get('output', {}).get('benefits', {}).get('value') not in [None, [], 'Not specified'])}/{len(matched)} jobs")
print(f"   - Posting Date: {sum(1 for j in matched if j.get('output', {}).get('posting_date', {}).get('value', 'Not specified') != 'Not specified')}/{len(matched)} jobs")
