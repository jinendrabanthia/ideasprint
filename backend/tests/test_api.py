import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI For Elders"
    assert "disclaimer" in data

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"

def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    paths = data["paths"]
    assert "/api/v1/auth/signup" in paths
    assert "/api/v1/auth/signin" in paths
    assert "/api/v1/reminders/" in paths
    assert "/api/v1/assistant/chat" in paths
    assert "/api/v1/checkins/today" in paths
    assert "/api/v1/contacts/" in paths
    assert "/api/v1/caregiver/dashboard" in paths
    assert "/api/v1/help" in paths

def test_unauthorized_endpoints():
    # Protected endpoints must require authorization
    assert client.get("/api/v1/profiles/me").status_code in (401, 403)
    assert client.get("/api/v1/reminders/").status_code in (401, 403)
    assert client.get("/api/v1/contacts/").status_code in (401, 403)
    assert client.get("/api/v1/caregiver/dashboard").status_code in (401, 403)
