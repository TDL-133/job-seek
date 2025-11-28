import pytest


class TestCompaniesAPI:
    """Tests for the companies API endpoints."""
    
    def test_list_companies_empty(self, client):
        """Test listing companies when database is empty."""
        response = client.get("/api/companies/")
        assert response.status_code == 200
        data = response.json()
        assert data["companies"] == []
        assert data["total"] == 0
    
    def test_create_company(self, client, sample_company_data):
        """Test creating a new company."""
        response = client.post("/api/companies/", json=sample_company_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_company_data["name"]
        assert data["industry"] == sample_company_data["industry"]
        assert data["id"] is not None
    
    def test_get_company(self, client, sample_company_data):
        """Test getting a specific company by ID."""
        # Create company first
        create_response = client.post("/api/companies/", json=sample_company_data)
        company_id = create_response.json()["id"]
        
        # Get the company
        response = client.get(f"/api/companies/{company_id}")
        assert response.status_code == 200
        assert response.json()["name"] == sample_company_data["name"]
    
    def test_update_company(self, client, sample_company_data):
        """Test updating a company."""
        # Create company first
        create_response = client.post("/api/companies/", json=sample_company_data)
        company_id = create_response.json()["id"]
        
        # Update the company
        update_data = {"rating": 4.8}
        response = client.put(f"/api/companies/{company_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["rating"] == 4.8
    
    def test_delete_company(self, client, sample_company_data):
        """Test deleting a company."""
        # Create company first
        create_response = client.post("/api/companies/", json=sample_company_data)
        company_id = create_response.json()["id"]
        
        # Delete the company
        response = client.delete(f"/api/companies/{company_id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(f"/api/companies/{company_id}")
        assert get_response.status_code == 404
    
    def test_list_companies_with_name_filter(self, client, sample_company_data):
        """Test listing companies with name filter."""
        # Create a company
        client.post("/api/companies/", json=sample_company_data)
        
        # Test name filter
        response = client.get("/api/companies/", params={"name": "Tech"})
        assert response.status_code == 200
        assert response.json()["total"] == 1
        
        # Test non-matching filter
        response = client.get("/api/companies/", params={"name": "NotFound"})
        assert response.status_code == 200
        assert response.json()["total"] == 0
