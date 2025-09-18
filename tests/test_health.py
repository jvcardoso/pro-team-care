import pytest
from fastapi.testclient import TestClient


class TestHealth:
    """Test suite para endpoints de health check"""

    def test_basic_health_check(self, client: TestClient):
        """Teste do health check básico"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Pro Team Care API"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_detailed_health_check(self, client: TestClient):
        """Teste do health check detalhado"""
        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["service"] == "Pro Team Care API"
        assert "checks" in data
        assert "database" in data["checks"]
        assert "memory" in data["checks"]
        assert "response_time_ms" in data

    def test_liveness_probe(self, client: TestClient):
        """Teste da liveness probe"""
        response = client.get("/api/v1/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness_probe(self, client: TestClient):
        """Teste da readiness probe"""
        response = client.get("/api/v1/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data
