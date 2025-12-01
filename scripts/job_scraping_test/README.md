# Job Search Pipeline - Complete Workflow

Complete job search system with 3-phase pipeline: URL collection, job extraction with location validation, and V2 scoring.

## Quick Start

**Single command to run everything:**

```bash
python run_job_search.py "Product Designer" "Lille" "Hauts-de-France"
```

This will:
1. ✅ Search all platforms (LinkedIn, Glassdoor, Indeed, WTTJ)
2. ✅ Extract job details + validate locations (Lille/Remote tags)
3. ✅ Score with V2 system (100 points, 6 categories)
4. ✅ Generate JSON + CSV outputs
5. ✅ Create summary report

## Architecture

### Phase 1: Multi-Platform URL Collection
**Script**: `test_phase1_only.py`  
**Input**: Job title, City, Region, Limit  
**Output**: `phase1_urls.json`, `phase1_urls.md`

**Features**:
- ✅ LinkedIn (Unipile API with auth)
- ✅ Glassdoor (Parallel Search + Tavily)
- ✅ Indeed (Firecrawl scraping)
- ✅ WTTJ (Firecrawl with title + location filtering)
- ✅ Parallel execution for speed
- ✅ Deduplication across sources

**WTTJ Optimization** (v1.6.1):
- Title matching: ≥2 key terms required
- Location filtering: 3-layer system (URL slugs → HTML context → proximity rules)
- Precision: Marseille test showed 31 → 2 jobs (100% accuracy)

### Phase 2: Job Details Extraction & Location Validation
**Script**: `extract_job_details.py`  
**Input**: `phase1_urls.json`, Target city  
**Output**: `phase2_jobs.json`, `phase2_jobs.csv`

**Extracted Fields**:
- Title, Company, Location, Salary, Contract Type
- Description (500 chars), Skills (up to 10)
- Platform, URL, Extraction timestamp

**Location Validation**:
- Target city detection (with metro area variations)
- Remote work detection
- Location tags: `Lille`, `Lille-Remote`, `Remote`, `Other`
- Confidence levels: High (2+ mentions) / Medium (1 mention) / Low

**Lille Test Results** (Product Designer):
- Total jobs: 59
- Lille-based: 9 (15.3%)
- Remote: 28 (47.5%)
- Other cities: 22 (37.2%)

### Phase 3: V2 Scoring System
**Script**: `score_jobs.py`  
**Input**: `phase2_jobs.json`, User preferences (optional)  
**Output**: `phase3_scored.json`, `phase3_scored.csv`

**Scoring Categories** (100 points total):
1. 🎭 **Role/Seniority** (35 pts): Junior/PM/Senior/Head detection
2. 🌍 **Geography** (25 pts): Remote/Hybrid/Office + city matching
3. 💰 **Salary** (15 pts): Linear interpolation €50k-€80k+
4. 🎯 **Skills** (20 pts): CV skills matching (job skills + description)
5. ✨ **Attractiveness** (10 pts): AI/impact/startup keywords
6. ⚠️ **Penalties** (-10 pts): No date, short desc, untrusted source

**Match Threshold**: ≥40 points = ✅ Match, <40 = 📋 À revoir

**Default Preferences** (Product Manager, Senior, Lille):
- Target seniority: Senior
- Preferred city: Lille
- Min salary: €60k
- Priority skills: Python, AI, ML, Product Strategy, Agile, Scrum
- CV skills: API, REST, SQL, Analytics, Data, Product Management
- Trusted sources: LinkedIn, Glassdoor, WTTJ (Indeed = untrusted)

## Usage

### Complete Workflow (Recommended)

```bash
# Basic search (10 jobs per platform)
python run_job_search.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes"

# Higher limit (20 jobs per platform)
python run_job_search.py "Data Analyst" "Paris" "Île-de-France" --limit 20

# With custom user preferences
python run_job_search.py "UX Designer" "Bordeaux" "Nouvelle-Aquitaine" --prefs user_prefs.json
```

### Individual Phases

**Phase 1 only:**
```bash
python test_phase1_only.py "Product Designer" "Lille" "Hauts-de-France" 10
```

**Phase 2 only** (requires Phase 1 output):
```bash
python extract_job_details.py Lille phase1_urls.json
```

**Phase 3 only** (requires Phase 2 output):
```bash
python score_jobs.py phase2_jobs.json
# Or with custom preferences:
python score_jobs.py phase2_jobs.json user_preferences.json
```

## Output Structure

```
results/
└── 20251130_143022_lille_product_designer/
    ├── phase1_urls.md             # Human-readable URL list
    ├── phase1_urls.json           # Structured URLs for Phase 2
    ├── phase2_jobs.json           # Full job details + location tags
    ├── phase2_jobs.csv            # CSV export of job details
    ├── phase3_scored.json         # Scored jobs with breakdown
    ├── phase3_scored.csv          # CSV export with scores
    └── SUMMARY.md                 # Final report
```

### JSON Schema Examples

**phase1_urls.json**:
```json
{
  "jobs": [
    {"url": "https://...", "platform": "LinkedIn"},
    {"url": "https://...", "platform": "Glassdoor"}
  ],
  "query": "Product Designer in Lille"
}
```

**phase2_jobs.json**:
```json
[
  {
    "title": "Senior Product Designer",
    "company": "TechCorp",
    "location": "59000 Lille",
    "location_tag": "Lille",
    "is_target_city": true,
    "is_remote": false,
    "salary": "50k-65k",
    "contract_type": "CDI",
    "description": "...",
    "skills": ["figma", "sketch", "user research"],
    "url": "https://...",
    "platform": "LinkedIn",
    "confidence": "high",
    "city_mentions": 3,
    "other_city_mentions": 0
  }
]
```

**phase3_scored.json**:
```json
[
  {
    "score": 72.5,
    "is_matched": true,
    "match_tag": "✅ Match",
    "breakdown": {
      "role": {"points": 25, "level": "senior"},
      "geography": {"points": 20, "type": "office_preferred"},
      "salary": {"points": 10.5, "salary": 57500},
      "skills": {"points": 15, "matched": 5},
      "attractiveness": {"points": 10, "level": "high"},
      "penalties": {"points": -8, "reasons": [...]}
    },
    "job_data": { /* full Phase 2 data */ }
  }
]
```

## User Preferences File Format

Create a JSON file for custom scoring preferences:

```json
{
  "preferred_city": "lyon",
  "target_seniority": "senior",
  "min_salary": 70000,
  "priority_skills": [
    "Python",
    "Machine Learning",
    "Product Strategy",
    "Agile",
    "SQL"
  ],
  "cv_skills": [
    "API Design",
    "REST",
    "Analytics",
    "Data Visualization",
    "Product Management",
    "User Research"
  ],
  "trusted_sources": {
    "linkedin": true,
    "glassdoor": true,
    "indeed": false,
    "wttj": true
  }
}
```

## API Keys Required

Create `.env` file in project root:

```bash
# Required for Phase 1
FIRECRAWL_API_KEY=fc-xxx          # Firecrawl for WTTJ/Indeed
UNIPILE_API_KEY=xxx               # LinkedIn authenticated search
UNIPILE_LINKEDIN_ACCOUNT_ID=xxx   # Your LinkedIn account
PARALLEL_API_KEY=xxx              # Parallel.ai for Glassdoor
TAVILY_API_KEY=xxx                # Tavily for Glassdoor fallback

# Optional for Phase 2 (falls back to httpx if missing)
# FIRECRAWL_API_KEY already defined above
```

## Performance Benchmarks

**Lille "Product Designer" search** (10 per source):
- Phase 1: ~30s (59 URLs found)
- Phase 2: ~2min (59 jobs extracted, 2s delay between scrapes)
- Phase 3: <1s (scoring is fast)
- **Total**: ~2.5 minutes

**Lyon "Product Manager" search** (unlimited):
- Phase 1: ~45s (150+ URLs found)
- Phase 2: ~5min (150+ jobs extracted)
- Phase 3: ~2s
- **Total**: ~6 minutes

## Integration with Job Seek App

The output is ready for integration:

1. **Phase 3 JSON** contains everything needed:
   - Full job details
   - Location tags (Lille/Remote/Other)
   - V2 scores with breakdown
   - Match status (✅/📋)

2. **Import to Database**:
   ```python
   import json
   from src.models import Job, JobScore
   
   with open('results/.../phase3_scored.json') as f:
       scored_jobs = json.load(f)
   
   for item in scored_jobs:
       job_data = item['job_data']
       # Create Job record
       job = Job(
           title=job_data['title'],
           company=job_data['company'],
           location=job_data['location'],
           # ... other fields
       )
       # Create JobScore record
       score = JobScore(
           job=job,
           score=item['score'],
           breakdown=item['breakdown']
       )
   ```

3. **Dashboard Display**:
   - Show all jobs sorted by score
   - Tag matched (≥40) vs unmatched (<40)
   - Allow toggle to show/hide unmatched
   - Display score breakdown on click

## Development

**Test Location Validation Only**:
```bash
python validate_lille_locations.py
```

**Run Individual Components**:
```bash
# Test WTTJ filtering
python parallel_scraper.py "Customer Success Manager" "Marseille" 10

# Test extraction
python extract_job_details.py Lille phase1_urls.json

# Test scoring
python score_jobs.py phase2_jobs.json
```

## Troubleshooting

**Phase 1 finds 0 WTTJ jobs**:
- This is normal if title + location filtering is working correctly
- WTTJ often returns off-target results that get filtered out
- Check logs for "31 jobs found → 0 passed filtering" message

**Phase 2 extraction fails**:
- Check API keys in `.env`
- Try running with `--verbose` flag
- Verify URLs are accessible (not behind login)

**Phase 3 all jobs score low**:
- Review user preferences (wrong target seniority?)
- Check skills list (too specific or mismatched?)
- Verify location tag (jobs tagged as "Other" lose 10-15 pts)

## File Manifest

**Core Scripts**:
- `run_job_search.py` - Main orchestrator
- `test_phase1_only.py` - Phase 1 (URL collection)
- `extract_job_details.py` - Phase 2 (extraction + location)
- `score_jobs.py` - Phase 3 (V2 scoring)

**Utilities**:
- `validate_lille_locations.py` - Standalone location validator
- `parallel_scraper.py` - Original scraper (v1.6.1)

**Documentation**:
- `README.md` - This file
- `METHODOLOGY.md` - Original Phase 1 documentation
- `CHANGELOG.md` - Version history
- `docs/PHASE1_WTTJ_OPTIMIZATION.md` - WTTJ filtering details
- `docs/SCORING_V2.md` - V2 scoring system spec

## Version History

- **v2.0.0** (2025-11-30): Complete 3-phase pipeline with orchestrator
- **v1.6.1** (2025-11-30): WTTJ title + location filtering
- **v1.6.0** (2025-11-29): Phase 1 with 4 platforms
- **v1.0.0** (2025-11-27): Initial parallel scraper

## Next Steps for Production

1. ✅ **Complete** - 3-phase pipeline working
2. ✅ **Complete** - Location validation (Lille/Remote tags)
3. ✅ **Complete** - V2 scoring system
4. 🔄 **In Progress** - Integration with Job Seek app
5. 📋 **TODO** - Real-time streaming (SSE) for Dashboard
6. 📋 **TODO** - Database import scripts
7. 📋 **TODO** - Scheduled batch jobs (daily/weekly)
8. 📋 **TODO** - User preferences UI in app

---

**Ready for integration into Job Seek app!** 🎯
