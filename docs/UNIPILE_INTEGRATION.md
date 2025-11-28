# Unipile LinkedIn Integration

## Overview
This document describes the integration of the Unipile API for authenticated LinkedIn job search in Job Seek. The integration replaces unreliable web scraping with the official Unipile API, providing more comprehensive and reliable job search results.

## Architecture

### Components
```
src/
├── services/
│   └── unipile.py          # Unipile API client service
└── scrapers/
    └── linkedin.py         # LinkedIn scraper (uses Unipile + fallback)
```

### Data Flow
1. User initiates job search via `/api/search/jobs` or `/api/search/scrape/linkedin`
2. `LinkedInScraper.search()` is called
3. If Unipile is configured, calls `UnipileService.search_jobs()`
4. Unipile API returns job listings from LinkedIn
5. Results are mapped to the internal Job schema
6. If Unipile fails/unconfigured, falls back to web scraping

## Configuration

### Environment Variables
Add to `.env`:
```bash
# Unipile API (for LinkedIn integration)
UNIPILE_DSN=https://api21.unipile.com:15160
UNIPILE_API_KEY=your-unipile-api-key
UNIPILE_LINKEDIN_ACCOUNT_ID=your-linkedin-account-id
```

### Getting Unipile Credentials
1. Sign up at [Unipile Dashboard](https://dashboard.unipile.com)
2. Connect your LinkedIn account
3. Copy your:
   - **DSN**: Base URL from dashboard (e.g., `https://api21.unipile.com:15160`)
   - **API Key**: Access token from dashboard
   - **Account ID**: Run `GET /api/v1/accounts` to find your LinkedIn account ID

## API Reference

### UnipileService Methods

#### `search_jobs(keywords, location, remote_only, experience_level, limit)`
Search for jobs on LinkedIn.

**Parameters:**
- `keywords` (str): Search terms (job title, skills)
- `location` (str, optional): Location filter
- `remote_only` (bool): Filter for remote jobs
- `experience_level` (str, optional): entry, mid, senior, director, executive
- `limit` (int): Max results (default 25)

**Returns:** List of job dictionaries

**Example:**
```python
from src.services.unipile import get_unipile_service

service = get_unipile_service()
jobs = await service.search_jobs(
    keywords="software engineer",
    location="Paris",
    remote_only=False,
    limit=20
)
```

#### `search_people(keywords, location, limit)`
Search for people on LinkedIn (for networking).

#### `get_profile(identifier)`
Get a LinkedIn profile by public ID or provider ID.

#### `get_relations(limit)`
Get all LinkedIn connections.

#### `check_account_status()`
Check the status of the connected LinkedIn account.

## Job Data Mapping

Unipile response fields are mapped to the Job model:

| Unipile Field | Job Model Field |
|---------------|-----------------|
| `title` | `title` |
| `company.name` | `company_name` |
| `location` | `location` |
| `workplace_type` | `remote_type` (mapped: remote/hybrid/onsite) |
| `job_url` | `source_url` |
| `id` | `external_id` |
| `easy_apply` | `easy_apply` (new field) |
| `posted_at` | `posted_at` |

## Rate Limits

Per [Unipile documentation](https://developer.unipile.com/docs/provider-limits-and-restrictions):

- **Search Results**: Max 1,000 profiles per day for classic LinkedIn
- **Profile Retrieval**: ~100 profiles per account per day
- **Best Practices**:
  - Random delays between requests (0.5-1.5s implemented)
  - Distribute calls across working hours
  - Start with low quantities for new accounts

## Error Handling

The integration includes:
1. **Configuration check**: `is_configured()` validates env vars before API calls
2. **Graceful fallback**: Falls back to web scraping if Unipile fails
3. **Request timeout**: 30-second timeout on API requests
4. **HTTP error handling**: Logs errors and returns empty results

## Testing

### Verify Unipile Configuration
```bash
curl --request GET \
  --url 'https://api21.unipile.com:15160/api/v1/accounts' \
  --header 'X-API-KEY:your-api-key' \
  --header 'accept: application/json'
```

### Test Job Search via API
```bash
curl -X POST 'http://localhost:8000/api/search/scrape/linkedin?keywords=software%20engineer&location=Paris&limit=5'
```

### Check Logs
```bash
docker-compose logs app | grep -i "linkedin\|unipile"
```

Expected output: `LinkedIn: Found X jobs via Unipile API`

## Troubleshooting

### "Unipile not configured" in logs
- Check that `UNIPILE_API_KEY` and `UNIPILE_LINKEDIN_ACCOUNT_ID` are set
- Verify the container has the env vars: `docker-compose exec app env | grep UNIPILE`

### Empty search results
- Verify LinkedIn account is connected in Unipile dashboard
- Check account status: `GET /api/v1/accounts` should show `status: "OK"`
- Try broader search terms

### 401/403 errors
- API key may be expired - regenerate in Unipile dashboard
- LinkedIn account may need re-authentication

## Future Enhancements

Potential additions:
- [ ] Job detail fetching (full descriptions)
- [ ] Location ID resolution for precise filtering
- [ ] Saved searches with cursor pagination
- [ ] Connection invitation sending
- [ ] InMail for premium accounts
- [ ] Webhook integration for real-time updates
