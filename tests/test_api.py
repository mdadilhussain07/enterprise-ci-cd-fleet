import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_service_info_endpoint():
    """Verify metadata endpoint returns correct version and status"""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "fleet-telemetry-service"
    assert data["version"] == "1.0.0"

def test_healthz_endpoint_structure():
    """Verify health endpoint schema adheres to orchestrator requirements"""
    response = client.get("/healthz")
    # In test environment without active DB, it will return 503 or 200 gracefully
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "uptime_seconds" in data
    assert "database" in data
    assert "environment" in data
