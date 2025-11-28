# Changelog - Job Seek

## [2025-11-28] - Major Update: V2 Scoring System & Real-Time Search

### 🎯 New Features

#### V2 Scoring System (100 points)
- **Fixed-point scoring** across 6 categories (replaces weighted scoring)
- Designed specifically for Product Manager job searches
- Categories:
  - 🎭 **Role/Seniority** (35 pts): Junior/PM/Senior/Head detection
  - 🌍 **Geography** (25 pts): Remote/Hybrid/Office + preferred city matching
  - 💰 **Salary** (15 pts): Linear interpolation €50k-€80k+
  - 🎯 **Skills** (20 pts): CV skills + priority skills matching
  - ✨ **Attractiveness** (10 pts): Mission-driven/startup keywords
  - ⚠️ **Penalties** (-10 pts): Quality issues (no date, short desc, untrusted source)

#### Real-Time Job Search with SSE
- **SearchPanel component** with keywords + city inputs
- **Server-Sent Events (SSE)** for live streaming updates
- Real-time platform scanning progress:
  - 🔄 LinkedIn: scanning...
  - ✅ LinkedIn: 12 offres trouvées
- Shows progress for all platforms: LinkedIn, Indeed, Glassdoor, WTTJ

#### Smart Job Display
- Display **ALL jobs** (not just matches)
- Visual tags:
  - ✅ **Match** (score ≥ 40): Green border, fully visible
  - 📋 **À revoir** (score < 40): Grey border, slightly faded
- Toggle to show/hide unmatched jobs
- Stats showing matched vs unmatched counts
- Re-scoring in real-time when criteria change

### 🔧 Technical Changes

#### Backend
- **New endpoint**: `GET /api/search/jobs/stream` (SSE streaming)
- **New endpoint**: `GET /api/health` (for nginx health checks)
- **New router**: `src/routers/criteria.py` - V2 preferences management
- **New service**: `src/services/scoring_v2.py` - Fixed-point scoring
- **New model**: `UserScoringPreferences` - V2 preferences storage
- Fixed `company_name` → `company.name` (relation)
- Fixed `posted_at` → `posted_date` (column name)
- Fixed None handling in scoring for missing job descriptions
- CORS updated to allow port 3001

#### Frontend
- **New component**: `SearchPanel.tsx` - Real-time search UI
- **New page**: `CriteriaV2.tsx` - V2 scoring configuration
- **Updated page**: `DashboardV2.tsx` - Integrated search + match tags
- API client updated to use relative URLs (`/api` instead of `http://localhost:8000/api`)
- Fixed SSE EventSource to work through nginx proxy

#### Infrastructure
- **Ports changed** to avoid conflicts:
  - Frontend: `3001` (was 3000)
  - Backend: `8001` (was 8000)
  - Can now run alongside other apps on 5173/8000
- Nginx proxy configuration updated
- Docker Compose updated for new ports

### 📝 Documentation
- Updated `WARP.md` with new ports and features
- Updated `docs/SCORING_V2.md` with search API documentation
- Created `CHANGELOG.md` (this file)

### 🔑 Test Credentials
```
Email: admin@jobseek.com
Password: admin12345678
```

### 🐛 Bug Fixes
- Fixed CORS errors by using nginx proxy for all API calls
- Fixed frontend login validation (8 chars minimum)
- Fixed Job model attribute errors (`company_name`, `posted_at`)
- Fixed scoring service to handle None descriptions

### 📦 Deployment
```bash
# Start Job Seek (all services)
docker-compose up -d

# Rebuild after changes
docker-compose up -d --build

# Access
- Frontend: http://localhost:3001
- Backend: http://localhost:8001
- API Docs: http://localhost:8001/docs
```

---

## Previous Versions

### [2025-11-27] - Initial V2 Implementation
- Basic V2 scoring system created
- Database models for preferences
- API endpoints for V2 scoring

### [Earlier] - V1 System
- Basic weighted scoring
- Job search across multiple platforms
- CV analysis with Anthropic API
- User profiles and authentication
