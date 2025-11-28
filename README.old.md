# Job Seek

A job search aggregator and application tracking system built with FastAPI and PostgreSQL.

## Features

- **Multi-platform Job Search**: Aggregate job listings from LinkedIn, Indeed, Glassdoor, and Welcome to the Jungle
- **Application Tracking**: Track your job applications through various stages (applied, interview, offer, etc.)
- **Company Database**: Store and manage company information
- **User Preferences**: Configure job search preferences (location, salary, remote work, etc.)
- **REST API**: Full-featured API for all operations

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Containerization**: Docker & Docker Compose
- **Web Scraping**: BeautifulSoup4, httpx, Selenium

## Quick Start

### Using Docker (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop the application
docker-compose down
```

The API will be available at `http://localhost:8000`

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start PostgreSQL (if not using Docker)
# Make sure PostgreSQL is running on port 5433

# Run the application
uvicorn src.main:app --reload
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Jobs
- `GET /api/jobs` - List jobs with filters
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs` - Create job listing
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job

### Applications
- `GET /api/applications` - List applications
- `GET /api/applications/stats` - Get application statistics
- `POST /api/applications` - Create application
- `PUT /api/applications/{id}` - Update application status
- `POST /api/applications/{id}/apply` - Mark as applied

### Search
- `POST /api/search/jobs` - Search jobs across platforms
- `POST /api/search/scrape/{platform}` - Scrape specific platform

### Companies
- `GET /api/companies` - List companies
- `POST /api/companies` - Add company
- `PUT /api/companies/{id}` - Update company

### Preferences
- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update preferences

## Project Structure

```
Job Seek/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── models/              # SQLAlchemy models
│   │   ├── job.py
│   │   ├── company.py
│   │   ├── application.py
│   │   └── user_preference.py
│   ├── routers/             # API route handlers
│   │   ├── jobs.py
│   │   ├── applications.py
│   │   ├── companies.py
│   │   ├── search.py
│   │   └── preferences.py
│   ├── schemas/             # Pydantic schemas
│   ├── scrapers/            # Web scrapers
│   │   ├── linkedin.py
│   │   ├── indeed.py
│   │   ├── glassdoor.py
│   │   └── wttj.py
│   └── services/            # Business logic
├── tests/                   # Test files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://... |
| ENVIRONMENT | development/production | development |
| API_HOST | API host | 0.0.0.0 |
| API_PORT | API port | 8000 |

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code
black src/ tests/

# Type checking
mypy src/
```

## MCP Tool Integration

This project is designed to work with MCP tools for enhanced scraping:
- **firecrawl**: For reliable web scraping
- **playwright**: For JavaScript-heavy sites
- **tavily**: For search functionality

Configure these tools in your Warp terminal for best results.

## License

MIT
