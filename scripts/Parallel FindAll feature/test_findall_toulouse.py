#!/usr/bin/env python3
"""
Test script for Parallel FindAll API - Product Manager jobs in Toulouse
"""
import time
import json
from parallel import Parallel

# API Configuration
API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"
FINDALL_BETA = "findall-2025-09-15"

client = Parallel(api_key=API_KEY)

def create_findall_run():
    """Create a FindAll run for Product Manager jobs in Toulouse"""
    print("🚀 Creating FindAll run for 'Product Manager' in Toulouse...")
    print("=" * 80)
    
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
        match_limit=100,  # Get ALL results
        betas=[FINDALL_BETA]
    )
    
    print(f"✅ Created FindAll run with ID: {findall_run.findall_id}")
    print(f"   Status: {findall_run.status.status}")
    print()
    return findall_run.findall_id

def poll_run_status(findall_id):
    """Poll the FindAll run until completion"""
    print("⏳ Polling run status...")
    print("=" * 80)
    
    terminal_statuses = ["completed", "failed", "cancelled"]
    status = "queued"
    iteration = 0
    
    while status not in terminal_statuses:
        iteration += 1
        findall_run = client.beta.findall.retrieve(
            findall_id=findall_id,
            betas=[FINDALL_BETA],
        )
        status = findall_run.status.status
        
        # Display status with progress metrics if available
        status_obj = findall_run.status
        metrics = []
        if hasattr(status_obj, 'generated_candidates_count'):
            metrics.append(f"Generated: {status_obj.generated_candidates_count}")
        if hasattr(status_obj, 'matched_candidates_count'):
            metrics.append(f"Matched: {status_obj.matched_candidates_count}")
        if hasattr(status_obj, 'unmatched_candidates_count'):
            metrics.append(f"Unmatched: {status_obj.unmatched_candidates_count}")
        
        metrics_str = " | ".join(metrics) if metrics else "No metrics yet"
        print(f"[{iteration}] Status: {status.upper():12} | {metrics_str}")
        
        if status not in terminal_statuses:
            time.sleep(10)
    
    print()
    print(f"🏁 Final status: {status.upper()}")
    print()
    return status

def get_results(findall_id):
    """Retrieve and display the FindAll results"""
    print("📊 Retrieving results...")
    print("=" * 80)
    
    run_result = client.beta.findall.result(
        findall_id=findall_id,
        betas=[FINDALL_BETA],
    )
    
    # Save full results to JSON
    result_data = run_result.model_dump()
    
    with open("toulouse_findall_results.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved full results to toulouse_findall_results.json")
    print()
    
    # Display summary
    matched = result_data.get('matched_candidates', [])
    unmatched = result_data.get('unmatched_candidates', [])
    
    print("📈 SUMMARY:")
    print(f"   Total Matched: {len(matched)}")
    print(f"   Total Unmatched: {len(unmatched)}")
    print()
    
    # Display matched jobs
    if matched:
        print("✅ MATCHED JOBS:")
        print("-" * 80)
        for idx, job in enumerate(matched, 1):
            print(f"\n{idx}. {job.get('name', 'N/A')}")
            print(f"   URL: {job.get('url', 'N/A')}")
            print(f"   Description: {job.get('description', 'N/A')[:100]}...")
            
            # Display match condition results
            output = job.get('output', {})
            for key, value in output.items():
                if isinstance(value, dict) and value.get('type') == 'match_condition':
                    match_status = "✓" if value.get('is_matched') else "✗"
                    print(f"   {match_status} {key}: {value.get('value', 'N/A')}")
    else:
        print("❌ No matched jobs found")
    
    print()
    return result_data

def main():
    """Main execution flow"""
    try:
        # Step 1: Create FindAll run
        findall_id = create_findall_run()
        
        # Step 2: Poll until completion
        status = poll_run_status(findall_id)
        
        # Step 3: Get results if completed
        if status == "completed":
            results = get_results(findall_id)
            print("🎉 FindAll run completed successfully!")
            print(f"   FindAll ID: {findall_id}")
            print(f"   Results saved to: toulouse_findall_results.json")
        else:
            print(f"⚠️  FindAll run ended with status: {status}")
            print(f"   FindAll ID: {findall_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
