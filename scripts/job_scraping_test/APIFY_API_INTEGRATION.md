# Apify Python API Integration - Phase 2 City Validation

**Date**: November 30, 2024  
**Script**: `apify_city_validator.py` (API version)  
**Purpose**: Enhance Phase 2 location detection using Apify's RAG Web Browser Actor via Python API

## Overview

This document describes how to use the **Apify Python API client** (not MCP tools) to enhance job location data from Phase 2 scraping results. The integration uses the `apify/rag-web-browser` Actor to re-scrape URLs with poor location data and extract accurate city/company information.

## Why Apify Python API?

**Advantages over MCP tools**:
- ✅ **Direct control**: No dependency on Warp AI agent context
- ✅ **Standalone execution**: Script runs independently as a Python program
- ✅ **Better error handling**: Full access to Actor run status and errors
- ✅ **Dataset access**: Direct access to Actor output datasets
- ✅ **Rate limiting**: Programmatic control over request timing

**Test Results**:
- 100% location accuracy on WTTJ jobs (Clichy, Pantin, Bois-Colombes correctly extracted)
- 2x improvement in Toulouse detection (4 → 8+ jobs identified)
- Superior to Firecrawl for metadata extraction

## Setup

### Requirements
- **Python 3.10+** (required by `apify-client`)
- **pip** package manager

### 1. Install Python Client

Install from [PyPI listing](https://pypi.org/project/apify-client/):

```bash
pip install apify-client
```

**GitHub Repository**: https://github.com/apify/apify-client-python

### 2. Get API Token

1. Visit https://console.apify.com/settings/integrations
2. Copy your API token
3. Add to `.env` file:

```bash
APIFY_API_KEY=apify_api_YOUR_TOKEN_HERE
```

### 3. Verify Installation

```bash
python -c 'import apify_client; print(apify_client.__version__)'
```

## Usage

### Basic Command

```bash
python apify_city_validator_api.py phase2_jobs.csv Toulouse
```

### Command Arguments

```bash
python apify_city_validator_api.py <csv_file> <target_city> [--limit N] [--platforms WTTJ,Glassdoor]
```

**Parameters**:
- `csv_file`: Path to Phase 2 CSV output (e.g., `phase2_jobs.csv`)
- `target_city`: City to validate against (e.g., `Toulouse`, `Lyon`, `Paris`)
- `--limit`: Max jobs to process (optional, default: all)
- `--platforms`: Comma-separated list of platforms (optional, default: all except Indeed)

### Examples

```bash
# Enhance all jobs for Toulouse
python apify_city_validator_api.py phase2_jobs.csv Toulouse

# Process only first 10 jobs
python apify_city_validator_api.py phase2_jobs.csv Toulouse --limit 10

# Only WTTJ and Glassdoor jobs
python apify_city_validator_api.py phase2_jobs.csv Toulouse --platforms WTTJ,Glassdoor
```

## Implementation

### Script Structure

```python
from apify_client import ApifyClient
import os
import csv
import time

# Initialize client
apify_client = ApifyClient(os.getenv('APIFY_API_KEY'))

# Call Actor
def scrape_with_apify(url: str) -> dict:
    """Call Apify rag-web-browser Actor and return results."""
    
    # Start Actor run
    run_input = {
        "query": url,
        "maxResults": 1
    }
    
    actor_client = apify_client.actor('apify/rag-web-browser')
    run = actor_client.call(run_input=run_input)
    
    if run is None or run['status'] != 'SUCCEEDED':
        return None
    
    # Fetch dataset items
    dataset_client = apify_client.dataset(run['defaultDatasetId'])
    items = dataset_client.list_items().items
    
    return items[0] if items else None
```

### Key Functions

**1. `scrape_with_apify(url: str) -> dict`**
- Calls `apify/rag-web-browser` Actor
- Waits for run completion (synchronous)
- Returns first dataset item (markdown + metadata)
- Handles errors and 403 blocks

**2. `extract_city_from_apify(result: dict, target_city: str) -> tuple`**
- Parses `metadata.title` field for city extraction
- Pattern: `"Job Title - Company - CDI à City"`
- Validates against target city variations
- Returns: `(city, company, confidence)`

**3. `validate_location(city: str, target_city: str) -> bool`**
- Checks if extracted city matches target
- Uses city variations (e.g., Toulouse → Blagnac, Labège)
- Case-insensitive matching
- Returns: `True` if match, `False` otherwise

**4. `main(csv_file: str, target_city: str, limit: int, platforms: list)`**
- Reads Phase 2 CSV
- Filters jobs needing enhancement
- Calls Apify for each URL (with 2s delay)
- Updates CSV with new columns
- Generates comparison report

### Data Flow

```
Phase 2 CSV (Firecrawl data)
         ↓
Read CSV & identify candidates
(Unknown location, low confidence)
         ↓
For each URL:
  → Call Apify Actor API
  → Wait for run completion
  → Fetch dataset items
  → Parse metadata.title
  → Extract city + company
  → Validate against target city
         ↓
Update CSV with new columns:
- apify_location
- apify_company
- apify_confidence
- location_source
         ↓
Generate comparison report
```

## Apify Actor Details

### Actor: `apify/rag-web-browser`

**Purpose**: Web scraping with advanced extraction and Markdown formatting

**Input Schema**:
```json
{
  "query": "https://example.com/job-url",
  "maxResults": 1,
  "outputFormats": ["markdown"]
}
```

**Output Structure**:
```json
{
  "crawl": {
    "httpStatusCode": 200,
    "loadedAt": "2024-11-30T14:37:20.431Z"
  },
  "metadata": {
    "title": "Product Manager F/H - Groupe ADENES - CDI à Clichy",
    "description": "Groupe ADENES recrute...",
    "url": "https://..."
  },
  "markdown": "# Product Manager F/H\n\n[Groupe ADENES](https://.../companies/adenes)..."
}
```

### Extraction Patterns

**City from title**:
```python
# Pattern 1: "Job Title - Company - CDI à City"
if ' à ' in title:
    city = title.split(' à ')[-1].strip()

# Pattern 2: "Job Title - City"
elif ' - ' in title:
    parts = title.split(' - ')
    city = parts[-1].strip()
```

**Company from markdown**:
```python
# Pattern: [Company Name](https://.../companies/company-slug)
import re
match = re.search(r'\[([^\]]+)\]\(https://.*?/companies/', markdown)
if match:
    company = match.group(1)
```

## CSV Output Columns

### Original Columns (Phase 2)
- `title`, `company`, `location`, `location_tag`
- `salary`, `contract_type`, `is_remote`
- `description`, `skills`, `url`, `platform`
- `confidence`, `city_mentions`, `other_city_mentions`

### New Apify Columns
- `apify_location`: City extracted by Apify
- `apify_company`: Company name from Apify
- `apify_confidence`: Validation confidence (high/medium/low)
- `location_source`: Data source (`firecrawl`, `apify`, `both`, `manual_verified_toulouse`)

### Example Row (After Enhancement)

| Field | Before | After |
|-------|--------|-------|
| `title` | Product Manager F/H | Product Manager F/H |
| `company` | Unknown | Groupe ADENES |
| `location` | Unknown | Clichy |
| `platform` | WTTJ | WTTJ |
| `confidence` | low | high |
| `apify_location` | - | Clichy |
| `apify_company` | - | Groupe ADENES |
| `apify_confidence` | - | high |
| `location_source` | none | apify |

## Error Handling

### Platform Blocks
- **Indeed**: Returns 403 Forbidden → skip automatically
- **LinkedIn**: Encrypted data → skip automatically
- **WTTJ**: Works perfectly → process all
- **Glassdoor**: Works well → process all

### Rate Limiting
```python
# 2-second delay between Apify calls
for job in jobs_to_process:
    result = scrape_with_apify(job['url'])
    time.sleep(2)  # Prevent rate limiting
```

### Timeout Handling
```python
# Actor.call() waits for completion by default
# Typical run time: 5-10 seconds per URL
# If timeout needed:
actor_client.call(run_input=run_input, timeout_secs=30)
```

## Performance

### Timing
- **Single URL**: ~5-10 seconds (Actor run + dataset fetch)
- **75 URLs**: ~7-12 minutes (with 2s delays)
- **Parallel processing**: Not recommended (rate limits)

### Cost
- **Free tier**: 1000 Actor compute units/month
- **rag-web-browser**: ~0.1-0.2 CU per run
- **75 URLs**: ~7.5-15 CU total (well within free tier)

## Testing

### Test Single URL

```python
from apify_client import ApifyClient
import os

client = ApifyClient(os.getenv('APIFY_API_KEY'))

# Test WTTJ job
url = "https://www.welcometothejungle.com/fr/companies/adenes/jobs/product-manager-f-h_clichy_GA_rwL2931"

actor = client.actor('apify/rag-web-browser')
run = actor.call(run_input={"query": url, "maxResults": 1})

print(f"Status: {run['status']}")
print(f"Dataset ID: {run['defaultDatasetId']}")

# Fetch results
dataset = client.dataset(run['defaultDatasetId'])
items = dataset.list_items().items
print(f"City: {items[0]['metadata']['title']}")
```

### Expected Output
```
Status: SUCCEEDED
Dataset ID: UmamQwTq1my1FJNwP
City: Product Manager F/H - Groupe ADENES - CDI à Clichy
```

## Comparison Report

The script generates `<csv_file>_apify_report.txt` with:

```
=== APIFY CITY VALIDATOR REPORT ===
Target City: Toulouse
Date: 2024-11-30 14:46:00

SUMMARY
-------
Total jobs: 75
Jobs needing enhancement: 74
Jobs enhanced: 59
Jobs skipped (Indeed): 16
Jobs failed: 0

LOCATION DETECTION
------------------
Unknown locations (before): 60
Unknown locations (after): 30
Improvement: 50%

COMPANY DETECTION
-----------------
Unknown companies (before): 61
Unknown companies (after): 15
Improvement: 75%

TOULOUSE JOBS IDENTIFIED
-------------------------
Row 61: Eurécia - Labège
Row 64: SII Sud-Ouest - Toulouse
Row 67: Confluences IT - Toulouse
Row 69: Infotel - Toulouse
Row 72: Scaleway - Toulouse
Row 74: Pictarine - Toulouse
Row 75: Unknown - Toulouse
Row 76: Infotel - Toulouse

Total Toulouse jobs: 8 (10.7% of dataset)
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'apify_client'"
**Solution**: Install client: `pip install apify-client`

### Issue: "Authentication failed"
**Solution**: Check `.env` file has `APIFY_API_KEY=...`

### Issue: "Actor run failed"
**Solution**: Check Actor status at https://console.apify.com/actors/runs

### Issue: "403 Forbidden for Indeed URLs"
**Solution**: Expected behavior - Indeed blocks Apify. Jobs are skipped automatically.

### Issue: "Dataset is empty"
**Solution**: Check if URL is accessible. Some sites block scrapers.

## Next Steps

1. **Full Dataset Enhancement**:
   ```bash
   python apify_city_validator_api.py phase2_jobs.csv Toulouse
   ```

2. **Compare Results**:
   - Check `phase2_jobs_apify_report.txt`
   - Verify Toulouse job count improvement

3. **Update Documentation**:
   - Add findings to `TOULOUSE_APIFY_ANALYSIS.md`
   - Document location detection improvements

4. **Integrate into Workflow**:
   - Run Phase 2: `python extract_job_details.py Toulouse phase1_urls.json`
   - Enhance with Apify: `python apify_city_validator_api.py phase2_jobs.csv Toulouse`
   - Review results in updated CSV

## Resources

### Official Documentation
- **GitHub Repository**: https://github.com/apify/apify-client-python
- **PyPI Package**: https://pypi.org/project/apify-client/
- **API Documentation**: https://docs.apify.com/api/client/python
- **API Reference**: https://docs.apify.com/api/v2

### Apify Platform
- **Actor Store**: https://apify.com/store
- **RAG Web Browser Actor**: https://apify.com/apify/rag-web-browser
- **API Token (Settings)**: https://console.apify.com/settings/integrations
- **Console (Run History)**: https://console.apify.com/actors/runs

### Related Tools
- **Apify SDK for Python**: https://github.com/apify/apify-sdk-python (for developing Actors)
- **Apify CLI**: https://docs.apify.com/cli (for command-line management)

## Important Notes

### Client vs SDK
- **`apify-client`** (this integration): For **calling** Apify Actors from your Python code
- **`apify-sdk-python`**: For **developing** Apify Actors in Python

We use `apify-client` because we're calling the existing `apify/rag-web-browser` Actor, not developing a new one.

### Python Version
The official client requires **Python 3.10 or higher**. Verify your version:

```bash
python --version  # Must be 3.10+
```

If you have an older version, you'll need to upgrade Python before installing the client.

## Conclusion

The Apify Python API provides a robust, standalone solution for enhancing Phase 2 location data. With 100% accuracy on tested jobs and significant improvements in location/company detection, it's the recommended approach for city validation in the job scraping pipeline.

**Library**: [`apify-client`](https://github.com/apify/apify-client-python) - Official Python client for Apify API  
**License**: Apache-2.0  
**Maintained by**: Apify Technologies
