"""Tests for health check endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test liveness probe returns healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_health_ready_endpoint(client):
    """Test readiness probe returns expected structure."""
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "timestamp" in data
    assert "postgres" in data["checks"]
    assert "redis" in data["checks"]
    assert "qdrant" in data["checks"]


def test_root_endpoint(client):
    """Test root endpoint returns app info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "MediLens AI"
    assert "version" in data
    assert data["status"] == "running"
