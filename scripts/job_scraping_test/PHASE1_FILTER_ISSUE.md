# Phase 1 Filtering Issue - Root Cause Analysis

## Current Results (Unbalanced)
```
- Glassdoor: 7 URLs
- WTTJ: 1 URL  
- Indeed: 130 URLs
- LinkedIn: 4 URLs
```

## Manual Search Baseline
```
- Indeed: 16 actual jobs
- WTTJ: 15 actual jobs
- Glassdoor: 27 actual jobs
```

## Root Cause

**We're mixing URL types**:

### Glassdoor (7 URLs)
✅ **Type**: Listing/search result pages (`SRCH_IL`, `SRCH_IC`)
- 7 listing pages collectively contain 27 individual job postings (~4 jobs per page average)
- Example: `https://www.glassdoor.com/Job/marseille-customer-success-manager-jobs-SRCH_IL...`
- **Problem**: We accept these pages but DON'T scrape them to extract individual jobs

### WTTJ (1 URL)
❌ **Type**: Mix of landing pages (404s) + 1 actual job
- 2 landing pages: `/pages/emploi-customer-success-manager-prov` (404 errors)
- 1 homepage: `/en` (not job-specific)
- 1 job post: `/companies/letsignit/jobs/customer-success-manager`
- **Problem**: Search APIs return category/landing pages instead of individual job URLs

### Indeed (130 URLs)
✅ **Type**: Individual job postings
- Extracted from 5 search pages via Firecrawl
- Each URL is a direct job posting: `/viewjob?jk=...`, `/rc/clk?jk=...`
- **Problem**: Too many results (130 vs 16 manual search), likely includes duplicates/unrelated jobs

## Solution

### 1. Glassdoor - Add 2-Step Extraction (Like Indeed)
**Current**: Accept 7 listing pages → Stop
**Needed**: Accept 7 listing pages → **Scrape each page** → Extract 27 total job URLs → Limit to 15-20 final jobs

**Implementation**:
```python
async def _firecrawl_scrape_glassdoor_listings(self, listing_urls: List[str]) -> List[str]:
    """
    Step 2 for Glassdoor: Scrape listing pages to extract individual job URLs.
    Similar to what we do for Indeed search pages.
    """
    all_job_urls = []
    for listing_url in listing_urls:
        # Scrape listing page with Firecrawl
        job_urls = extract_job_urls_from_page(listing_url)
        all_job_urls.extend(job_urls)
    return all_job_urls[:15]  # Limit to 15 jobs
```

### 2. WTTJ - Better Search Strategy
**Current**: Getting landing pages `/pages/...` (404s)
**Needed**: Target company job pages directly

**Options**:
1. Use WTTJ API if available
2. Search for specific company pages: `site:welcometothejungle.com/fr/companies/*/jobs/*`
3. Add Firecrawl search specifically for WTTJ like we do for Indeed

### 3. Indeed - Deduplicate & Validate
**Current**: 130 URLs from 5 search pages
**Needed**: 
1. Deduplicate URLs (remove duplicates across pages)
2. Validate each job actually matches "Customer Success Manager" + "Marseille"
3. Limit to 15-20 jobs max

**Implementation**:
```python
# After extracting Indeed URLs
unique_indeed = list(set(indeed_urls))  # Deduplicate
validated_indeed = validate_job_match(unique_indeed, job_title, city)  # Validate
final_indeed = validated_indeed[:15]  # Limit
```

## Expected Results After Fix

```
- Glassdoor: 15-20 individual job URLs (from 27 total across 7 listing pages)
- WTTJ: 10-15 individual job URLs (with better search)
- Indeed: 15-20 individual job URLs (deduplicated & validated from 130)
- LinkedIn: 4 jobs (already working)
---
Total: ~44-59 jobs across all sources
```

## Priority Actions

1. **HIGH**: Add Glassdoor listing page scraping (2-step like Indeed)
2. **HIGH**: Fix Indeed deduplication (130 → 15-20)
3. **MEDIUM**: Improve WTTJ search to find actual job postings
4. **LOW**: Add validation that jobs match query (title + location)

## Technical Notes

- Glassdoor listing pages follow same pattern as Indeed search pages
- Both need scraping to extract individual job URLs
- The imbalance (7 vs 130) is because we scrape Indeed but not Glassdoor
- Fix: Apply same 2-step process to both sources
- Glassdoor: 7 listing pages contain 27 jobs total (~4 jobs/page, vs Indeed ~26 jobs/page)
