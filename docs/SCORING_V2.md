# Scoring System V2 - Fixed Point System for PM Jobs

## Overview

The V2 scoring system uses a fixed-point allocation across 6 categories, designed specifically for Product Manager job searches. Total possible score: 100 points (with up to -10 penalty deductions).

## Categories & Point Allocation

### 🎭 Role/Seniority (35 points max)
Points are awarded based on the detected seniority level in the job title:

| Level | Points | Detection Patterns |
|-------|--------|-------------------|
| Junior | 8 | "junior product manager", "associate PM", "APM", "product analyst" |
| PM | 15 | "product manager", "product owner", "PM" |
| Senior | 25 | "senior product manager", "sr. PM", "lead PM", "staff PM" |
| Head/VP | 35 | "head of product", "VP product", "director of product", "CPO" |

Detection order: Head → Senior → PM → Junior (first match wins)

### 🌍 Geography/Remote (25 points max)
Points based on location match and remote work options:

| Scenario | Points |
|----------|--------|
| Full remote anywhere | 25 |
| Hybrid in preferred city | 22 |
| Office in preferred city | 20 |
| Hybrid in other city | 15 |
| Office in other city | 10 |

User configures their preferred city in preferences.

### 💰 Salary (15 points max)
Linear interpolation based on job salary:

| Salary Range | Points |
|--------------|--------|
| €80k+ | 15 |
| €60k-€80k | 10-15 (linear) |
| €50k-€60k | 5-10 (linear) |
| <€50k | 0-5 (linear) |
| Not disclosed | 7 (neutral) |

### 🎯 Skills Match (20 points max)
Based on how many user skills match job requirements:

| Matches | Points |
|---------|--------|
| 10+ skills | 20 |
| 5-9 skills | 15-20 (linear) |
| 2-4 skills | 10-15 (linear) |
| <2 skills | 0-10 (linear) |

Skills are matched from:
- User's CV-extracted skills
- User's priority skills (manually added)

Matching checks both job skills list and job description text.

### ✨ Attractiveness (10 points max)
Based on company/job keywords indicating attractiveness:

| Level | Points | Keywords |
|-------|--------|----------|
| High (Mission-driven) | 10 | AI, ML, climate, sustainability, impact, healthtech, biotech, unicorn, Series B/C |
| Medium (Growing startup) | 6 | startup, scale-up, Series A, fintech, edtech, fast-growing, innovative |
| Low (Regular company) | 2 | Default if no keywords match |

### ⚠️ Penalties (-10 points max)
Deductions for quality issues:

| Issue | Penalty |
|-------|---------|
| No posting date | -5 |
| Short description (<100 chars) | -3 |
| Untrusted source | -2 |

Users can mark job sources as trusted/untrusted in preferences.

## API Endpoints

### Preferences
```
GET  /api/criteria/preferences/v2     - Get user preferences
PUT  /api/criteria/preferences/v2     - Update preferences
POST /api/criteria/preferences/v2/reset - Reset to defaults
```

### Source Trust
```
PUT /api/criteria/preferences/v2/sources/{source} - Toggle source trust
    Body: {"trusted": true/false}
```

### Priority Skills
```
POST   /api/criteria/preferences/v2/skills        - Add skill
DELETE /api/criteria/preferences/v2/skills/{name} - Remove skill
```

### Scored Jobs
```
GET /api/jobs/scored/v2              - List jobs with scores (sorted by score desc)
    Query params: skip, limit, title, location, remote_type, min_score

GET /api/jobs/{id}/score/v2          - Get score breakdown for single job
```

## Response Format

### Score Breakdown
```json
{
  "score": 85.5,
  "breakdown": {
    "role": {
      "points": 25,
      "max": 35,
      "level": "senior",
      "label": "Senior",
      "details": "Detected: Senior ✓ (matches target)"
    },
    "geography": {
      "points": 25,
      "max": 25,
      "type": "remote",
      "details": "Full remote 🏠"
    },
    "salary": {
      "points": 12.5,
      "max": 15,
      "salary": 70000,
      "details": "€70k ✓"
    },
    "skills": {
      "points": 15,
      "max": 20,
      "matched": 5,
      "matched_skills": ["python", "sql", "agile"],
      "details": "python, sql, agile (+2 more)"
    },
    "attractiveness": {
      "points": 10,
      "max": 10,
      "level": "high",
      "matched_keywords": ["ai", "impact"],
      "details": "Mission-driven: ai, impact"
    },
    "penalties": {
      "points": -2,
      "max": -10,
      "reasons": ["Untrusted source: indeed (-2)"],
      "details": "Untrusted source: indeed (-2)"
    }
  }
}
```

## User Preferences Schema
```json
{
  "preferred_city": "Toulouse",
  "min_salary": 60000,
  "target_seniority": "senior",
  "priority_skills": ["Python", "AI/ML", "Product Strategy"],
  "trusted_sources": {
    "linkedin": true,
    "indeed": true,
    "glassdoor": true,
    "welcometothejungle": true
  },
  "attractiveness_keywords": {
    "high": ["ai", "climate", "impact", ...],
    "medium": ["startup", "fintech", ...],
    "custom": []
  }
}
```

## Frontend Pages

### /criteria
New CriteriaV2 page with 6 sections:
1. **Role/Seniority selector** - Radio buttons for target level
2. **Geography** - City input + remote preference explanation
3. **Salary** - Minimum salary input
4. **Skills** - CV skills display + priority skills management
5. **Attractiveness** - Keywords explanation (read-only for now)
6. **Sources** - Toggle trusted/untrusted per source

### /dashboard
New DashboardV2 page showing:
- **Search Panel** with keywords and city inputs
- Real-time streaming search with SSE showing platform progress:
  - 🔄 LinkedIn: scanning...
  - ✅ LinkedIn: 12 offres trouvées
- Jobs sorted by V2 score
- **Match tags**: 
  - ✅ Match (score ≥ 40) - green border
  - 📋 À revoir (score < 40) - grey border, slightly faded
- Toggle to show/hide unmatched jobs
- Seniority badge on each job card
- Quick score tags (geography, salary, skills, attractiveness, penalties)
- Expandable full score breakdown panel
- Score filter (Tous, 40+, 60+, 80+)
- Stats showing matched vs unmatched counts

## Search API

### Streaming Search (SSE)
```
GET /api/search/jobs/stream
    Query params: keywords, location, platforms (comma-separated), save_results
    
    Returns Server-Sent Events:
    - scanning_start: {event, platform}
    - scanning_complete: {event, platform, count, jobs[]}
    - error: {event, platform, message}
    - search_complete: {event, total, platforms_searched[]}
```

Example:
```bash
curl "http://localhost:8000/api/search/jobs/stream?keywords=Product%20Manager&location=Paris"
```
