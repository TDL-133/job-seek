# Phase 1 WTTJ Optimization

## Overview

WTTJ (Welcome to the Jungle) search results include "suggested" jobs from various cities even when searching for a specific location (e.g., Marseille). This document describes the optimization implemented to filter WTTJ results by **both job title AND location** during Phase 1 URL collection.

## Problem Statement

**Before optimization:**
- Query: "Customer Success Manager" in "Marseille"
- WTTJ returns: 31 jobs
- Actual relevant jobs: ~2-6 (mostly Paris, Lyon, and unrelated titles)

**Issues:**
1. **Title mismatch**: Search returns Business Developer, Project Manager, and other non-Customer Success roles
2. **Location mismatch**: Majority of jobs are in Paris/Lyon despite searching for Marseille
3. **Mixed suggestions**: WTTJ algorithm includes national suggestions even with location specified

## Solution Architecture

### Two-Stage Filtering

#### Stage 1: Title Filtering
Filters jobs by title relevance using keyword matching:

**Implementation** (`_match_job_title` method):
1. Strip Firecrawl search highlights (e.g., `_Customer_` → `Customer`)
2. Extract key terms from query and scraped title (length > 2, excluding stop words)
3. Match if ≥2 terms overlap (case-insensitive)
4. Stop words: `h, f, hf, fn, mfd, cdi, stage, alternance, de, le, la, et, ou, in, at, the, a, an`

**Example:**
- Query: "Customer Success Manager"
- Match: "Customer Success Specialist F/H" ✓ (customer, success match)
- Reject: "Business Developer Manager" ✗ (only manager matches)

#### Stage 2: Location Filtering
Filters jobs by geographic location using URL slug + HTML context:

**Implementation** (`_firecrawl_search_wttj` method):

**Priority 1: URL Slug (Authoritative)**
- Check for `_{city}` in URL (e.g., `_marseille`, `_paris`)
- **Reject** if URL explicitly contains a different city (e.g., `_lyon` when searching Marseille)
- Support nearby cities (for Marseille: Aix-en-Provence, Aubagne, Salon)

**Priority 2: HTML Context Location (Fallback)**
- Extract location mentions from markdown (pattern: `\n[City]\n` or `\n[City1, City2]\n`)
- Filter to known French cities (50+ cities in whitelist)
- Map URLs to locations using HTML proximity (±1000 chars)
- Accept if target city found in extracted location

**City Whitelist:**
```
paris, marseille, lyon, toulouse, nice, nantes, strasbourg, montpellier, bordeaux, 
lille, rennes, reims, toulon, grenoble, dijon, angers, nîmes, villeurbanne, 
clermont, aix, brest, tours, amiens, limoges, annecy, perpignan, metz, besançon, 
orleans, mulhouse, rouen, caen, nancy, argenteuil, saint, montreuil, roubaix, 
tourcoing, avignon, poitiers, versailles, courbevoie, vitry, créteil, pau, la, 
cannes, antibes, puteaux, boulogne, rambouillet, aubagne, salon
```

## Results

### Marseille Query Performance

| Stage | Jobs Count | Description |
|-------|-----------|-------------|
| Initial | 31 | All WTTJ search results |
| After Title Filter | 8 | Customer Success roles only |
| After Location Filter | 2 | Marseille-based Customer Success jobs |

### Final Output

**Kept Jobs:**
1. Walter Learning - Customer Success Specialist F/H (Marseille)
2. Walter Learning - Customer Success Specialist F/H (Marseille) [variant]

**Rejected:**
- 6 Paris-based Customer Success jobs
- 23 unrelated titles (Business Developer, Project Manager, etc.)

## Code Location

**File:** `scripts/job_scraping_test/parallel_scraper.py`

**Key Methods:**
- `_match_job_title(query_title, scraped_title, min_terms=2)` - Lines 351-379
- `_firecrawl_search_wttj(job_title, city, region, max_results)` - Lines 452-625

## Configuration

### Customization Points

1. **Minimum term matches** (line 351): Default 2, increase for stricter title matching
2. **Stop words** (line 364): Add language-specific or domain-specific terms
3. **City whitelist** (lines 514-523): Add/remove cities based on target regions
4. **Nearby cities** (lines 591, 605, 618): Customize regional proximity

### Platform Support

Currently optimized for **French job market**:
- French city names with accents (é, è, ê)
- French job title variations (H/F, CDI, Stage, Alternance)
- French stop words

## Testing

**Test Script:** `scripts/job_scraping_test/test_phase1_only.py`

**Expected Output:**
```
✓ Found 31 WTTJ jobs before filtering
✓ Kept 2/31 WTTJ jobs after title+location filtering
```

**Validation:**
```bash
cd "/Users/lopato/Documents/DAGORSEY/Geek/Job Seek"
/path/to/venv/bin/python scripts/job_scraping_test/test_phase1_only.py
cat phase1_urls.md | grep -A 5 "## WTTJ"
```

## Limitations

1. **HTML context accuracy**: Location extraction from HTML proximity can be imprecise for jobs without city suffix in URL
2. **Multi-location jobs**: Jobs with multiple locations may be rejected if primary location doesn't match target
3. **Language-specific**: Currently optimized for French; requires adaptation for other markets
4. **Firecrawl dependency**: Requires Firecrawl API for markdown/HTML extraction

## Future Improvements

1. **Semantic title matching**: Use embeddings instead of keyword matching
2. **Region-based filtering**: Accept jobs in broader regions (e.g., Provence-Alpes-Côte d'Azur)
3. **Multi-location support**: Parse and validate all job locations, not just primary
4. **Confidence scoring**: Return match confidence instead of binary accept/reject
5. **A/B testing**: Track filtering accuracy vs. recall to optimize thresholds

## Related Documentation

- [SCRAPING_INTEGRATION.md](./SCRAPING_INTEGRATION.md) - Scraping service setup
- [WARP.md](../WARP.md) - Development environment guide
- Phase 1 test results: `phase1_urls.md`
