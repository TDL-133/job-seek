import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.models.base import Base, get_db


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "title": "Software Engineer",
        "description": "Build amazing software",
        "location": "Paris, France",
        "remote_type": "hybrid",
        "salary_min": 50000,
        "salary_max": 70000,
        "salary_currency": "EUR",
        "job_type": "full-time",
        "experience_level": "mid",
        "source_url": "https://example.com/job/123",
        "source_platform": "linkedin",
        "skills": ["python", "fastapi", "postgresql"],
    }


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "name": "Tech Corp",
        "description": "A great tech company",
        "website": "https://techcorp.com",
        "headquarters": "Paris, France",
        "industry": "Technology",
        "company_size": "51-200",
        "rating": 4.5,
    }


@pytest.fixture
def sample_application_data():
    """Sample application data for testing."""
    return {
        "job_id": 1,
        "status": "saved",
        "notes": "Looks promising",
        "next_action": "Apply online",
    }
