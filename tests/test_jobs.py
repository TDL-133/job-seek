import pytest


class TestJobsAPI:
    """Tests for the jobs API endpoints."""
    
    def test_list_jobs_empty(self, client):
        """Test listing jobs when database is empty."""
        response = client.get("/api/jobs/")
        assert response.status_code == 200
        data = response.json()
        assert data["jobs"] == []
        assert data["total"] == 0
    
    def test_create_job(self, client, sample_job_data):
        """Test creating a new job."""
        response = client.post("/api/jobs/", json=sample_job_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_job_data["title"]
        assert data["location"] == sample_job_data["location"]
        assert data["id"] is not None
    
    def test_create_duplicate_job(self, client, sample_job_data):
        """Test that duplicate jobs (same URL) are rejected."""
        # Create first job
        response = client.post("/api/jobs/", json=sample_job_data)
        assert response.status_code == 200
        
        # Try to create duplicate
        response = client.post("/api/jobs/", json=sample_job_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_get_job(self, client, sample_job_data):
        """Test getting a specific job by ID."""
        # Create job first
        create_response = client.post("/api/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]
        
        # Get the job
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["title"] == sample_job_data["title"]
    
    def test_get_nonexistent_job(self, client):
        """Test getting a job that doesn't exist."""
        response = client.get("/api/jobs/9999")
        assert response.status_code == 404
    
    def test_update_job(self, client, sample_job_data):
        """Test updating a job."""
        # Create job first
        create_response = client.post("/api/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]
        
        # Update the job
        update_data = {"title": "Senior Software Engineer"}
        response = client.put(f"/api/jobs/{job_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["title"] == "Senior Software Engineer"
    
    def test_delete_job(self, client, sample_job_data):
        """Test deleting a job."""
        # Create job first
        create_response = client.post("/api/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]
        
        # Delete the job
        response = client.delete(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(f"/api/jobs/{job_id}")
        assert get_response.status_code == 404
    
    def test_list_jobs_with_filters(self, client, sample_job_data):
        """Test listing jobs with filters."""
        # Create a job
        client.post("/api/jobs/", json=sample_job_data)
        
        # Test title filter
        response = client.get("/api/jobs/", params={"title": "Software"})
        assert response.status_code == 200
        assert response.json()["total"] == 1
        
        # Test non-matching filter
        response = client.get("/api/jobs/", params={"title": "Manager"})
        assert response.status_code == 200
        assert response.json()["total"] == 0
