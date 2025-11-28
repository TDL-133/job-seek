# Job Seek - Methodology

## Project Approach

### Architecture Decisions

#### 1. FastAPI Framework
- **Why**: Modern, async-first Python framework with automatic OpenAPI documentation
- **Benefits**: High performance, type hints, automatic validation, great developer experience

#### 2. PostgreSQL Database
- **Why**: Robust relational database for structured job data
- **Benefits**: JSON support for flexible fields (skills, benefits), strong indexing, reliable

#### 3. SQLAlchemy 2.0
- **Why**: Industry-standard Python ORM with async support
- **Benefits**: Type safety, migration support (Alembic), flexible querying

#### 4. Docker Compose
- **Why**: Consistent development environment
- **Benefits**: Easy setup, isolated PostgreSQL, reproducible builds

### Data Model Design

#### Jobs Table
- Core job listing information (title, description, location)
- Salary range with currency support
- Source tracking (URL, platform, external ID)
- Skills and benefits as JSON arrays for flexibility
- Active status for soft deletion

#### Applications Table
- Status enum for application pipeline tracking
- Interview scheduling fields
- Contact information storage
- Notes and follow-up tracking
- Outcome tracking (offer amount, rejection reason)

#### Companies Table
- Company metadata (size, industry, founded year)
- Multiple location support via JSON
- Rating integration (from Glassdoor, etc.)
- Culture keywords for matching

#### User Preferences Table
- Job search criteria (titles, keywords, locations)
- Salary and remote work preferences
- Excluded companies list
- Alert settings

### Scraping Strategy

#### Multi-Platform Approach
Each platform has a dedicated scraper class inheriting from `BaseScraper`:
- `LinkedInScraper` - Public jobs API/page
- `IndeedScraper` - Job search results
- `GlassdoorScraper` - Jobs with company ratings
- `WTTJScraper` - European tech focus

#### Scraper Design Principles
1. **Async by default** - All scrapers use `httpx` for async HTTP
2. **Graceful degradation** - Multiple selectors for each element
3. **MCP tool ready** - Designed for enhancement with firecrawl/playwright
4. **Deduplication** - Jobs identified by source URL

#### Rate Limiting Considerations
- Built-in tenacity for retry logic
- Selenium available for JavaScript-heavy sites
- User-agent rotation capability

### API Design

#### RESTful Endpoints
- Standard CRUD operations for all resources
- Pagination with skip/limit parameters
- Filtering via query parameters
- Stats endpoints for dashboards

#### Search Endpoint
- Accepts multiple platforms
- Concurrent scraping with asyncio.gather
- Optional database persistence
- Error handling per-platform

### Future Enhancements

1. **Frontend**: React/Vue dashboard for visual tracking
2. **Notifications**: Email alerts for new matching jobs
3. **AI Integration**: Resume matching, cover letter generation
4. **Analytics**: Application success rate tracking
5. **Calendar Integration**: Interview scheduling sync
6. **Browser Extension**: One-click job saving
