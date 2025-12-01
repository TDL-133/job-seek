#!/usr/bin/env python3
"""
Quick script to check if enrichments are complete and fetch results
"""
import json
from parallel import Parallel

API_KEY = "TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv"
FINDALL_BETA = "findall-2025-09-15"
FINDALL_ID = "findall_3b9bcb767a82472fa75824227c820bed"

client = Parallel(api_key=API_KEY)

print("🔍 Checking enrichment status...")
print(f"   FindAll ID: {FINDALL_ID}")
print()

try:
    result = client.beta.findall.result(
        findall_id=FINDALL_ID,
        betas=[FINDALL_BETA]
    )
    
    # Check if enrichments are present
    matched = [c for c in result.candidates if c.match_status == "matched"]
    print(f"✅ Found {len(matched)} matched jobs")
    
    if matched:
        first_job = matched[0]
        output_keys = list(first_job.output.keys())
        
        enrichment_fields = [
            "salary_range", "company_size", "experience_level", "industry",
            "required_skills", "contract_type", "remote_policy",
            "languages_required", "benefits", "posting_date"
        ]
        
        found_enrichments = [f for f in enrichment_fields if f in output_keys]
        
        if found_enrichments:
            print(f"\n🎉 ENRICHMENTS COMPLETE!")
            print(f"   Found {len(found_enrichments)}/10 enrichment fields:")
            for field in found_enrichments:
                print(f"   ✓ {field}")
            
            # Save results
            print("\n📊 Saving enriched results...")
            result_data = result.model_dump()
            with open("toulouse_enriched_results.json", "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print("✅ Saved to toulouse_enriched_results.json")
            print("\n📋 Sample job data (first one):")
            print(f"   Title: {first_job.name}")
            for field in found_enrichments[:5]:  # Show first 5 fields
                if field in first_job.output:
                    value = first_job.output[field].get('value', 'N/A')
                    if isinstance(value, list):
                        value = ", ".join(value[:3])  # Show first 3 items
                    print(f"   {field}: {value}")
            
            print("\n✨ Next step: Run export_enriched_to_csv.py to create spreadsheet")
        else:
            print("\n⏳ Enrichments still processing...")
            print("   No enrichment fields found yet in output")
            print(f"   Current output keys: {output_keys}")
            print("\n💡 Wait a few more minutes and run this script again")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 The enrichment may still be processing")
    print("   Check https://app.parallel.ai for status")
