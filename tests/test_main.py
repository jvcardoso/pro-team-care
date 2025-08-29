import os
import pytest
from fastapi.testclient import TestClient

# Set test environment
os.environ["ENV_FILE"] = ".env.test"

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Pro Team Care API"
    assert data["version"] == "1.0.0"

def test_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200

def test_openapi_json():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert data["info"]["title"] == "Pro Team Care API"