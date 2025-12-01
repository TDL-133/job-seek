# How to Add Salary & Company Size to FindAll Results

## Overview
FindAll API supports **enrichments** - additional data extraction that runs AFTER the initial job matching. This allows you to add fields like:
- 💰 **Salary Range**
- 🏢 **Company Size**
- 📄 **Contract Type** (CDI, CDD, Stage, etc.)
- 🏠 **Remote Policy** (Full Remote, Hybrid, On-site)

## Two-Step Process

### Step 1: Run FindAll (Normal Search)
First, run the standard FindAll search to find all matching jobs:
```python
findall_run = client.beta.findall.create(
    objective="Find all jobs for product manager in Toulouse, France...",
    entity_type="jobs",
    match_conditions=[...],
    generator="core",
    match_limit=100
)
```

Wait for completion (~13 minutes for 29 jobs).

### Step 2: Add Enrichments
Once the run completes, add enrichments to extract additional data:
```python
client.beta.findall.enrich(
    findall_id=findall_id,
    enrichments=[
        {
            "processor": "core",  # Use 'core' for best quality
            "output_schema": {
                "type": "json",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "salary_range": {
                            "type": "string",
                            "description": "Salary range in EUR (e.g., '45,000 - 55,000 EUR')"
                        },
                        "company_size": {
                            "type": "string",
                            "description": "Company size: 'Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1001-5000)', 'Enterprise (5000+)'"
                        },
                        "contract_type": {
                            "type": "string",
                            "description": "CDI, CDD, Stage, Freelance, or Not specified"
                        },
                        "remote_policy": {
                            "type": "string",
                            "description": "Full Remote, Hybrid, On-site, or Not specified"
                        }
                    }
                }
            }
        }
    ]
)
```

Wait for enrichment to complete (~5-10 minutes for 29 jobs).

## Quick Start

### Option 1: Run with Enrichments (Recommended)
```bash
cd "/Users/lopato/Documents/DAGORSEY/Geek/Job Seek/scripts/Parallel FindAll feature"
python3 test_findall_with_enrichments.py
```

This will:
1. Create FindAll run
2. Wait for completion
3. Add enrichments automatically
4. Save to `toulouse_enriched_results.json`
5. Show sample results

**Total time:** ~20-25 minutes (13 min search + 7-12 min enrichments)

### Option 2: Add Enrichments to Existing Run
If you already have a completed FindAll run, you can add enrichments to it:

```python
from parallel import Parallel

client = Parallel(api_key="YOUR_API_KEY")

# Use your existing findall_id
client.beta.findall.enrich(
    findall_id="findall_3b9bcb767a82472f8ee31f45325ee9ba",  # Your existing run
    enrichments=[...],  # Same schema as above
    betas=["findall-2025-09-15"]
)
```

## Export to CSV

After enrichments complete:
```bash
python3 export_enriched_to_csv.py
```

This creates `toulouse_enriched_results.csv` with columns:
1. Job Title
2. Company
3. Location
4. **Salary Range** ⭐ NEW
5. **Company Size** ⭐ NEW
6. **Contract Type** ⭐ NEW
7. **Remote Policy** ⭐ NEW
8. URL
9. Role Type
10. Source
11. Description

## Expected Results

### Salary Information
The AI will extract salary ranges like:
- "50,000 - 55,000 EUR" (from MyUnisoft posting)
- "45,000 - 60,000 EUR" (estimated from role/location)
- "Not specified" (if no salary info available)

### Company Size
Categories detected from company info:
- "Startup (1-50)" - Small startups
- "Small (51-200)" - Small businesses
- "Medium (201-1000)" - Mid-size companies
- "Large (1001-5000)" - Large corporations (e.g., Sopra Steria)
- "Enterprise (5000+)" - Major enterprises (e.g., Airbus, Thales)
- "Unknown" - If not mentioned

### Contract Type
- "CDI" - Most permanent positions
- "CDD" - Fixed-term contracts
- "Stage" - Internships (like Airbus 2026)
- "Freelance" - Contractor roles
- "Not specified" - Unknown

### Remote Policy
- "Hybrid" - Mix of office/remote (most common in Toulouse)
- "On-site" - Full office presence
- "Full Remote" - 100% remote
- "Not specified" - Not mentioned

## Pricing

**Enrichments cost extra** on top of base FindAll:
- Base FindAll: ~$6-8 (29 matches with core generator)
- Enrichments: ~$2-4 per field per job
- **Total estimate:** $10-15 for 29 jobs with 4 enrichment fields

**Cost breakdown:**
- Each enrichment runs as a separate Task API call
- Core processor: ~$0.10-0.15 per enrichment per job
- 29 jobs × 4 fields × $0.12 = ~$14

## Tips

1. **Test with Preview First**: Use `generator="preview"` to test enrichments on ~10 jobs before full run
2. **Fewer Fields = Lower Cost**: Only request enrichments you actually need
3. **Cache Results**: Enriched data is saved in JSON, no need to re-run
4. **Use Core Processor**: Better quality than 'base', worth the extra cost

## Files Created

After running with enrichments:
- ✅ `toulouse_enriched_results.json` - Full data with enrichments
- ✅ `toulouse_enriched_results.csv` - Spreadsheet with all fields
- ✅ `test_findall_with_enrichments.py` - Script to run enrichments
- ✅ `export_enriched_to_csv.py` - Script to export to CSV

## Example Output

```
1. Product Owner (H/F) Solutions TPE/PME – MyUnisoft
   💰 Salary: 50,000 - 55,000 EUR
   🏢 Company Size: Small (51-200)
   📄 Contract: CDI
   🏠 Remote: Hybrid

2. Product Manager – Sopra Steria
   💰 Salary: Not specified
   🏢 Company Size: Enterprise (5000+)
   📄 Contract: CDI
   🏠 Remote: Hybrid
```

## Next Steps

1. Run `python3 test_findall_with_enrichments.py` to get enriched data
2. Open `toulouse_enriched_results.csv` in Excel/Sheets
3. Filter by salary range, company size, or remote policy
4. Apply to jobs that match your criteria!

## Documentation

- FindAll Enrichments: https://docs.parallel.ai/findall-api/features/findall-enrich
- Task API (used for enrichments): https://docs.parallel.ai/task-api/task-quickstart
- Output Schemas: https://docs.parallel.ai/task-api/guides/specify-a-task#output-schema
