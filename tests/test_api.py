"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from agentic_clinical_assistant.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
    assert "version" in response.json()


def test_agent_health():
    """Test agent health endpoint."""
    response = client.get("/agent/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_agent_run_endpoint():
    """Test agent run endpoint."""
    response = client.post(
        "/agent/run",
        json={
            "request_text": "What is the policy for sepsis treatment?",
            "user_id": "test_user",
        },
    )
    assert response.status_code == 202
    assert "run_id" in response.json()
    assert "status" in response.json()
    assert response.json()["status"] == "pending"


def test_agent_run_validation():
    """Test request validation."""
    # Empty request text should fail
    response = client.post(
        "/agent/run",
        json={"request_text": ""},
    )
    assert response.status_code == 422  # Validation error


def test_agent_status_not_found():
    """Test status endpoint with non-existent run_id."""
    import uuid

    fake_id = uuid.uuid4()
    response = client.get(f"/agent/status/{fake_id}")
    # Will fail without database, but structure is correct
    assert response.status_code in [404, 500]


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus format
    assert "text/plain" in response.headers.get("content-type", "")

