from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from .models import Base, engine
from .routers import jobs, applications, companies, search, preferences
from .routers import auth, profile, criteria, blacklist


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Job Seek API",
    description="API for intelligent job search with CV analysis and weighted scoring",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Auth & Profile
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(criteria.router, prefix="/api/criteria", tags=["Scoring Criteria"])
app.include_router(blacklist.router, prefix="/api/blacklist", tags=["Blacklist"])

# Include routers - Jobs & Search
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(preferences.router, prefix="/api/preferences", tags=["Preferences"])


@app.get("/")
async def root():
    return {
        "message": "Job Seek API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy"}
