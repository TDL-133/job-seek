import pytest


class TestApplicationsAPI:
    """Tests for the applications API endpoints."""
    
    def test_list_applications_empty(self, client):
        """Test listing applications when database is empty."""
        response = client.get("/api/applications/")
        assert response.status_code == 200
        data = response.json()
        assert data["applications"] == []
        assert data["total"] == 0
    
    def test_create_application(self, client, sample_job_data, sample_application_data):
        """Test creating a new application."""
        # First create a job
        job_response = client.post("/api/jobs/", json=sample_job_data)
        job_id = job_response.json()["id"]
        
        # Create application
        sample_application_data["job_id"] = job_id
        response = client.post("/api/applications/", json=sample_application_data)
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "saved"
    
    def test_get_application_stats(self, client):
        """Test getting application statistics."""
        response = client.get("/api/applications/stats")
        assert response.status_code == 200
        data = response.json()
        # Should have all status types
        assert "saved" in data
        assert "applied" in data
        assert "interview" in data
    
    def test_update_application_status(self, client, sample_job_data, sample_application_data):
        """Test updating application status."""
        # Create job and application
        job_response = client.post("/api/jobs/", json=sample_job_data)
        job_id = job_response.json()["id"]
        
        sample_application_data["job_id"] = job_id
        app_response = client.post("/api/applications/", json=sample_application_data)
        app_id = app_response.json()["id"]
        
        # Update status
        update_data = {"status": "applied"}
        response = client.put(f"/api/applications/{app_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "applied"
    
    def test_mark_as_applied(self, client, sample_job_data, sample_application_data):
        """Test marking application as applied."""
        # Create job and application
        job_response = client.post("/api/jobs/", json=sample_job_data)
        job_id = job_response.json()["id"]
        
        sample_application_data["job_id"] = job_id
        app_response = client.post("/api/applications/", json=sample_application_data)
        app_id = app_response.json()["id"]
        
        # Mark as applied
        response = client.post(f"/api/applications/{app_id}/apply")
        assert response.status_code == 200
        assert response.json()["status"] == "applied"
        assert response.json()["applied_at"] is not None
