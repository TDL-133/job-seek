# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

### Docker (Primary)
```bash
# Start all services (backend + frontend + db)
docker-compose up -d

# Rebuild after code changes (REQUIRED after any src/ or frontend/ changes)
docker-compose up -d --build

# View logs
docker-compose logs -f app       # Backend logs
docker-compose logs -f frontend  # Frontend logs

# Stop/Reset
docker-compose down           # Stop containers
docker-compose down -v        # Stop + delete database volume
```

### Backend Local Development
```bash
source venv/bin/activate
uvicorn src.main:app --reload --port 8001
```

### Frontend Local Development
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5174
```

### Testing
```bash
pytest tests/ -v                          # All tests
pytest tests/test_jobs.py -v              # Single file
pytest tests/test_jobs.py::test_name -v   # Single test
```

### Code Quality
```bash
black src/ tests/    # Format
mypy src/            # Type check
```

## Architecture

### Backend Structure
```
src/
├── main.py           # FastAPI app, lifespan, router registration
├── routers/          # API endpoints (auth, profile, criteria, blacklist, jobs, etc.)
├── models/           # SQLAlchemy models (User, UserProfile, ScoringCriteria, etc.)
├── schemas/          # Pydantic request/response models
├── scrapers/         # Platform scrapers inheriting BaseScraper
└── services/         # Business logic (AuthService, CVAnalysisService, ScoringService, etc.)
```

### Frontend Structure
```
frontend/src/
├── App.tsx           # React Router configuration
├── pages/            # Page components (Landing, Login, Dashboard, Criteria, etc.)
├── components/       # Reusable UI components (layout/Sidebar, layout/MainLayout)
├── services/api.ts   # Axios API client with auth interceptors
├── store/            # Zustand stores (authStore)
└── types/            # TypeScript interfaces
```

### Key Backend Patterns

**Database Sessions**: Use `get_db` dependency from `src/models/base.py`
```python
from src.models.base import get_db
@router.get("/")
def list_items(db: Session = Depends(get_db)):
```

**Authentication**: Use `get_current_user` dependency from `src/routers/auth.py`
```python
from src.routers.auth import get_current_user
@router.get("/")
def protected_endpoint(current_user: User = Depends(get_current_user)):
```

**Scrapers**: Inherit from `BaseScraper`, implement async `search()` method

### Ports
**Docker (Production)**:
- Frontend: http://localhost:3001
- Backend: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Database: Port 5433

**Local Dev**:
- Frontend: http://localhost:5174
- Backend: http://localhost:8001

### Database
- PostgreSQL 15 on port 5433 (local) / 5432 (docker internal)
- Credentials: `jobseek:jobseek_password@localhost:5433/jobseek_db`
- Tables auto-created via `Base.metadata.create_all()` in lifespan

### Environment Variables
Required in `.env`:
- `JWT_SECRET_KEY` - For auth token signing
- `ANTHROPIC_API_KEY` - For CV analysis and cover letter generation
- `UNIPILE_DSN` - Unipile API base URL (default: https://api21.unipile.com:15160)
- `UNIPILE_API_KEY` - Unipile API access token
- `UNIPILE_LINKEDIN_ACCOUNT_ID` - Connected LinkedIn account ID in Unipile

### LinkedIn Integration (Unipile)
The app uses Unipile API for authenticated LinkedIn job search:
- Service: `src/services/unipile.py` - UnipileService class
- Scraper: `src/scrapers/linkedin.py` - Uses Unipile with web scraping fallback
- Rate limits: ~1000 job searches/day, respect random delays between requests
- API docs: https://developer.unipile.com/reference

### Scraping Services (Indeed, Glassdoor, WTTJ)
The app uses professional scraping services with fallback strategy:
- Service: `src/services/scraping_service.py` - Centralized scraping with 3 methods
- Strategy: Firecrawl → BrightData → httpx (in order of preference)
- Optional API keys in `.env`:
  - `FIRECRAWL_API_KEY` - Fast scraping with anti-bot bypass (https://firecrawl.dev/)
  - `BRIGHTDATA_API_KEY` - Professional scraping with rotating proxies (https://brightdata.com/)
- Fallback: Simple httpx if no API keys configured
- Docs: `docs/SCRAPING_INTEGRATION.md`

### Test Setup
Tests use in-memory SQLite via `tests/conftest.py`

## API Endpoints
- Docs: http://localhost:8001/docs
- Health: GET `/health` and GET `/api/health`
- Auth: `/api/auth/` (register, login, me)
- Profile: `/api/profile/` (CRUD, CV upload)
- Criteria V2: `/api/criteria/preferences/v2` (V2 scoring system)
- Blacklist: `/api/blacklist/` (CRUD)
- Jobs: `/api/jobs/` (list, search, score)
- Jobs V2: `/api/jobs/scored/v2` (V2 scoring with breakdown)
- Search: `/api/search/jobs` (standard search)
- Search SSE: `/api/search/jobs/stream` (real-time streaming search)
- FindAll Status: `/api/search/status/{findall_id}` (polling for background search status)

## Frontend URLs
- Landing: `/`
- Login: `/login`
- Register: `/register`
- Onboarding (CV Upload): `/onboarding`
- Profile: `/profile`
- Criteria Config V2: `/criteria` (V2 scoring system with 6 categories)
- Dashboard V2: `/dashboard` (with real-time job search)
- Blacklist: `/blacklist`
- Settings: `/settings`

## Test Credentials
```
Email: admin@jobseek.com
Password: admin12345678
```

## Key Features

### V2 Scoring System (100 points)
6 fixed-point categories for PM jobs:
- 🎭 Role/Seniority (35 pts): Junior/PM/Senior/Head detection
- 🌍 Geography (25 pts): Remote/Hybrid/Office + city matching
- 💰 Salary (15 pts): Linear interpolation €50k-€80k+
- 🎯 Skills (20 pts): CV skills matching (job skills + description)
- ✨ Attractiveness (10 pts): AI/impact/startup keywords
- ⚠️ Penalties (-10 pts): No date, short desc, untrusted source

See `docs/SCORING_V2.md` for full documentation.

### Real-Time Job Search (FindAll)
- Search Panel with keywords + location inputs
- Server-Sent Events (SSE) streaming for real-time progress
- **Persistent tracking**: Progress saved to localStorage (`jobseek_active_findall`)
- **Background polling**: If SSE disconnects, polls `/api/search/status/{id}` every 5s
- **Resume capability**: Returns results even if page was refreshed during search
- Live stats: generated candidates count + matched offers count
- Job cards with circular score ring (Excellent/Bien/Moyen/Faible)

## Color Scheme
Primary: Coral/Terracotta (#e07a5f / #c85544)
Configured in `frontend/tailwind.config.js`
