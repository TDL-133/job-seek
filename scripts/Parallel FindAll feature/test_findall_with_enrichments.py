#!/usr/bin/env python3
"""
Test script for Parallel FindAll API with ENRICHMENTS
Adds salary range and company size to job results
"""
import time
import json
from parallel import Parallel

# API Configuration
API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"
FINDALL_BETA = "findall-2025-09-15"

client = Parallel(api_key=API_KEY)

def create_findall_run_with_enrichments():
    """Create a FindAll run with enrichments for salary and company size"""
    print("🚀 Creating FindAll run with ENRICHMENTS...")
    print("=" * 80)
    
    # Step 1: Create the base FindAll run (same as before)
    findall_run = client.beta.findall.create(
        objective="Find all jobs for product manager in Toulouse, France on Glassdoor, Welcome to the Jungle, Indeed, and LinkedIn websites",
        entity_type="jobs",
        match_conditions=[
            {
                "name": "product_manager_role_check",
                "description": "Job must be for a 'product manager' or related role (Product Owner, PM, etc.)."
            },
            {
                "name": "toulouse_france_location_check",
                "description": "Job must be located in Toulouse, France."
            },
            {
                "name": "job_board_check",
                "description": "Job must be listed on Glassdoor, Welcome to the Jungle (welcometothejungle.com), Indeed, or LinkedIn websites."
            }
        ],
        generator="core",
        match_limit=100,
        betas=[FINDALL_BETA]
    )
    
    findall_id = findall_run.findall_id
    print(f"✅ Created FindAll run: {findall_id}")
    print()
    
    # Step 2: Poll until completion
    print("⏳ Waiting for run to complete...")
    status = "queued"
    terminal_statuses = ["completed", "failed", "cancelled"]
    
    while status not in terminal_statuses:
        time.sleep(10)
        findall_run = client.beta.findall.retrieve(
            findall_id=findall_id,
            betas=[FINDALL_BETA]
        )
        status = findall_run.status.status
        print(f"   Status: {status.upper()}")
    
    if status != "completed":
        print(f"❌ Run failed with status: {status}")
        return
    
    print("✅ Base run completed!")
    print()
    
    # Step 3: Add enrichments for matched jobs
    print("🔍 Adding ENRICHMENTS (salary + company size)...")
    print("=" * 80)
    
    enrichment_result = client.beta.findall.enrich(
        findall_id=findall_id,
        enrichments=[
            {
                "processor": "core",  # Use 'core' for better quality
                "output_schema": {
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
                            "contract_type": {
                                "type": "string",
                                "description": "Type of employment contract: 'CDI' (permanent), 'CDD' (fixed-term), 'Stage' (internship), 'Freelance', or 'Not specified'."
                            },
                            "remote_policy": {
                                "type": "string",
                                "description": "Remote work policy: 'Full Remote', 'Hybrid', 'On-site', or 'Not specified'. Look for télétravail, remote, hybrid mentions."
                            }
                        },
                        "required": ["salary_range", "company_size", "contract_type", "remote_policy"],
                        "additionalProperties": False
                    }
                }
            }
        ],
        betas=[FINDALL_BETA]
    )
    
    print("✅ Enrichment request submitted!")
    print(f"   This will extract salary, company size, contract type, and remote policy")
    print(f"   for all {len([c for c in findall_run.candidates if c.match_status == 'matched'])} matched jobs")
    print()
    
    # Step 4: Poll again for enrichment completion
    print("⏳ Waiting for enrichments to complete...")
    print("   (This may take several minutes as each job is analyzed)")
    print()
    
    enriched = False
    poll_count = 0
    
    while not enriched and poll_count < 120:  # Max 20 minutes
        time.sleep(10)
        poll_count += 1
        
        result = client.beta.findall.result(
            findall_id=findall_id,
            betas=[FINDALL_BETA]
        )
        
        # Check if enrichments are present in output
        matched_candidates = [c for c in result.candidates if c.match_status == "matched"]
        if matched_candidates:
            first_output = matched_candidates[0].output
            # Check if enrichment fields exist
            if any(key in first_output for key in ["salary_range", "company_size"]):
                enriched = True
                print(f"✅ Enrichments completed after ~{poll_count * 10} seconds!")
                break
        
        if poll_count % 6 == 0:  # Print every minute
            print(f"   Still enriching... ({poll_count * 10}s elapsed)")
    
    if not enriched:
        print("⚠️  Enrichment timeout - results may be incomplete")
    
    print()
    
    # Step 5: Get final results with enrichments
    print("📊 Retrieving enriched results...")
    final_result = client.beta.findall.result(
        findall_id=findall_id,
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
        print(f"   URL: {job['url'][:60]}...")
        
        output = job.get('output', {})
        
        # Show enrichment data
        if 'salary_range' in output:
            salary = output['salary_range'].get('value', 'N/A')
            print(f"   💰 Salary: {salary}")
        
        if 'company_size' in output:
            size = output['company_size'].get('value', 'N/A')
            print(f"   🏢 Company Size: {size}")
        
        if 'contract_type' in output:
            contract = output['contract_type'].get('value', 'N/A')
            print(f"   📄 Contract: {contract}")
        
        if 'remote_policy' in output:
            remote = output['remote_policy'].get('value', 'N/A')
            print(f"   🏠 Remote: {remote}")
    
    print("\n" + "=" * 80)
    print(f"\n✅ COMPLETE! Found {len(matched)} jobs with enrichments")
    print(f"   - Salary ranges extracted")
    print(f"   - Company sizes identified")
    print(f"   - Contract types parsed")
    print(f"   - Remote policies detected")
    print()
    print(f"📁 Results saved to: toulouse_enriched_results.json")
    print(f"💡 Run 'python3 export_enriched_to_csv.py' to create CSV with all fields")
    print("=" * 80)

if __name__ == "__main__":
    create_findall_run_with_enrichments()
