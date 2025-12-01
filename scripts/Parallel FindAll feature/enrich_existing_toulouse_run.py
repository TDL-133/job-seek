#!/usr/bin/env python3
"""
Add enrichments to the existing Toulouse FindAll run
Run ID: findall_3b9bcb767a82472fa75824227c820bed
"""
import time
import json
from parallel import Parallel

# API Configuration
API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"
FINDALL_BETA = "findall-2025-09-15"

# Your existing completed run
FINDALL_ID = "findall_3b9bcb767a82472fa75824227c820bed"

client = Parallel(api_key=API_KEY)

def enrich_existing_run():
    """Add enrichments to existing completed FindAll run"""
    print("🚀 Adding enrichments to existing Toulouse run")
    print(f"   FindAll ID: {FINDALL_ID}")
    print("=" * 80)
    
    # Step 1: Verify run exists and is completed
    print("\n📋 Checking run status...")
    try:
        findall_run = client.beta.findall.retrieve(
            findall_id=FINDALL_ID,
            betas=[FINDALL_BETA]
        )
        status = findall_run.status.status
        print(f"   ✓ Run found with status: {status.upper()}")
        
        if status != "completed":
            print(f"   ⚠️  Warning: Run status is '{status}', not 'completed'")
            print(f"   Enrichments may not work on non-completed runs")
            response = input("\n   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("   Aborted.")
                return
    except Exception as e:
        print(f"   ❌ Error retrieving run: {e}")
        return
    
    # Count matched jobs from status metrics
    matched_count = findall_run.status.metrics.matched_candidates_count
    print(f"   ✓ Found {matched_count} matched jobs to enrich")
    print()
    
    # Step 2: Add comprehensive enrichments
    print("🔍 Adding ENRICHMENTS...")
    print("=" * 80)
    print("\nEnrichment fields:")
    print("  1. 💰 Salary Range")
    print("  2. 🏢 Company Size")
    print("  3. 🎓 Experience Level")
    print("  4. 🏭 Industry/Sector")
    print("  5. 🛠️  Required Skills")
    print("  6. 📄 Contract Type")
    print("  7. 🏠 Remote Policy")
    print("  8. 🌐 Languages Required")
    print("  9. 🎁 Benefits/Perks")
    print(" 10. 📅 Posting Date")
    print()
    
    try:
        enrichment_result = client.beta.findall.enrich(
            findall_id=FINDALL_ID,
            processor="core",  # Use 'core' for best quality
            output_schema={
                "type": "json",
                "json_schema": {
                    "type": "object",
                    "properties": {
                                "salary_range": {
                                    "type": "string",
                                    "description": "The salary range for this position in euros (EUR). Format as 'XX,000 - YY,000 EUR' or 'Not specified' if not mentioned. Look for salary information in the job description, title, or any visible compensation details."
                                },
                                "company_size": {
                                    "type": "string",
                                    "description": "The size of the company hiring. Use categories: 'Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1001-5000)', 'Enterprise (5000+)', or 'Unknown' if not specified. Look for employee count, company description, or industry context."
                                },
                                "experience_level": {
                                    "type": "string",
                                    "description": "Required experience level: 'Junior (0-2 years)', 'Mid-level (3-5 years)', 'Senior (5-8 years)', 'Lead/Principal (8+ years)', or 'Not specified'. Look for years of experience, seniority indicators, or role level."
                                },
                                "industry": {
                                    "type": "string",
                                    "description": "Primary industry or sector: 'SaaS', 'FinTech', 'E-commerce', 'HealthTech', 'Aerospace', 'Consulting', 'Banking', 'Retail', 'Manufacturing', 'Public Sector', or 'Unknown'. Identify from company description or context."
                                },
                                "required_skills": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of key technical and soft skills required. Include: methodologies (Agile, Scrum, Lean), tools (JIRA, Figma, Confluence), technical skills (SQL, API, Analytics), and PM skills (Roadmapping, Stakeholder Management). Return empty array if none specified."
                                },
                                "contract_type": {
                                    "type": "string",
                                    "description": "Type of employment contract: 'CDI' (permanent/indefinite), 'CDD' (fixed-term), 'Stage' (internship), 'Freelance', 'Alternance' (apprenticeship), or 'Not specified'."
                                },
                                "remote_policy": {
                                    "type": "string",
                                    "description": "Remote work policy: 'Full Remote' (100% remote), 'Hybrid' (mix of office and remote), 'On-site' (full office presence), or 'Not specified'. Look for télétravail, remote, hybrid, or office presence mentions."
                                },
                                "languages_required": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Required languages with proficiency level. Format as 'Language (Level)', e.g., 'French (Native)', 'English (Fluent)', 'Spanish (Professional)'. Return empty array if not specified."
                                },
                                "benefits": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Key benefits and perks offered. Common in France: 'RTT' (extra days off), 'Ticket Restaurant' (meal vouchers), 'Mutuelle' (health insurance), 'Stock Options', 'Gym/Sport', 'Training Budget', 'Flexible Hours', 'Bike Allowance'. Return empty array if none mentioned."
                                },
                                "posting_date": {
                                    "type": "string",
                                    "description": "How long ago the job was posted. Format as 'X days ago', 'X weeks ago', 'X months ago', or 'Not specified' if unclear. Look for posting date, publication date, or freshness indicators."
                                }
                            },
                            "required": [
                                "salary_range",
                                "company_size", 
                                "experience_level",
                                "industry",
                                "required_skills",
                                "contract_type",
                                "remote_policy",
                                "languages_required",
                                "benefits",
                                "posting_date"
                            ],
                            "additionalProperties": False
                        }
            },
            betas=[FINDALL_BETA]
        )
        
        print("✅ Enrichment request submitted successfully!")
        print(f"   Enriching {matched_count} matched jobs with 10 data fields")
        print()
        
    except Exception as e:
        print(f"❌ Error submitting enrichment: {e}")
        return
    
    # Step 3: Poll for enrichment completion
    print("⏳ Waiting for enrichments to complete...")
    print("   (This will take ~5-15 minutes for 29 jobs with 10 fields)")
    print("   You can check progress at: https://app.parallel.ai")
    print()
    
    enriched = False
    poll_count = 0
    max_polls = 180  # 30 minutes max
    
    while not enriched and poll_count < max_polls:
        time.sleep(10)
        poll_count += 1
        
        try:
            result = client.beta.findall.result(
                findall_id=FINDALL_ID,
                betas=[FINDALL_BETA]
            )
            
            # Check if enrichments are present in output
            matched_candidates = [c for c in result.candidates if c.match_status == "matched"]
            if matched_candidates:
                first_output = matched_candidates[0].output
                # Check if enrichment fields exist
                enrichment_fields = ["salary_range", "company_size", "experience_level", "industry"]
                if any(key in first_output for key in enrichment_fields):
                    enriched = True
                    print(f"\n✅ Enrichments completed after ~{poll_count * 10} seconds!")
                    break
            
            if poll_count % 6 == 0:  # Print every minute
                elapsed = poll_count * 10
                print(f"   [{elapsed}s] Still enriching... (typically takes 5-15 minutes)")
        
        except Exception as e:
            print(f"   ⚠️  Polling error: {e}")
            time.sleep(10)
    
    if not enriched:
        print("\n⚠️  Timeout reached. Enrichments may still be processing.")
        print("   Check status at: https://app.parallel.ai")
        print("   Run this script again later to fetch completed enrichments.")
        return
    
    print()
    
    # Step 4: Get and save enriched results
    print("📊 Retrieving enriched results...")
    final_result = client.beta.findall.result(
        findall_id=FINDALL_ID,
        betas=[FINDALL_BETA]
    )
    
    # Save to JSON
    result_data = final_result.model_dump()
    with open("toulouse_enriched_results.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Saved enriched results to toulouse_enriched_results.json")
    print()
    
    # Display sample enrichments
    print("📋 SAMPLE ENRICHED JOBS (first 3):")
    print("-" * 80)
    
    matched = [c for c in result_data["candidates"] if c["match_status"] == "matched"]
    for i, job in enumerate(matched[:3], 1):
        print(f"\n{i}. {job['name']}")
        
        output = job.get('output', {})
        
        # Show all enrichment data
        if 'salary_range' in output:
            print(f"   💰 Salary: {output['salary_range'].get('value', 'N/A')}")
        
        if 'company_size' in output:
            print(f"   🏢 Company Size: {output['company_size'].get('value', 'N/A')}")
        
        if 'experience_level' in output:
            print(f"   🎓 Experience: {output['experience_level'].get('value', 'N/A')}")
        
        if 'industry' in output:
            print(f"   🏭 Industry: {output['industry'].get('value', 'N/A')}")
        
        if 'required_skills' in output:
            skills = output['required_skills'].get('value', [])
            if skills and isinstance(skills, list):
                print(f"   🛠️  Skills: {', '.join(skills[:5])}")
        
        if 'contract_type' in output:
            print(f"   📄 Contract: {output['contract_type'].get('value', 'N/A')}")
        
        if 'remote_policy' in output:
            print(f"   🏠 Remote: {output['remote_policy'].get('value', 'N/A')}")
        
        if 'languages_required' in output:
            langs = output['languages_required'].get('value', [])
            if langs and isinstance(langs, list):
                print(f"   🌐 Languages: {', '.join(langs)}")
        
        if 'benefits' in output:
            benefits = output['benefits'].get('value', [])
            if benefits and isinstance(benefits, list):
                print(f"   🎁 Benefits: {', '.join(benefits[:4])}")
        
        if 'posting_date' in output:
            print(f"   📅 Posted: {output['posting_date'].get('value', 'N/A')}")
    
    print("\n" + "=" * 80)
    print(f"\n✅ COMPLETE! Enriched {len(matched)} jobs with 10 data fields")
    print()
    print("📁 Files created:")
    print("   - toulouse_enriched_results.json (full data)")
    print()
    print("💡 Next step: Run CSV export")
    print("   python3 export_enriched_to_csv.py")
    print()
    print(f"💰 Estimated cost: ~$25-35 for 29 jobs × 10 fields")
    print("=" * 80)

if __name__ == "__main__":
    enrich_existing_run()
