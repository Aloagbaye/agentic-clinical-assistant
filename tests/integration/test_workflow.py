"""Integration tests for complete workflow."""

import pytest
import requests
import time


@pytest.fixture
def api_url():
    """API base URL."""
    return "http://localhost:8000"


@pytest.mark.integration
def test_complete_workflow(api_url):
    """Test complete agent workflow end-to-end."""
    # Create agent run
    response = requests.post(
        f"{api_url}/agent/run",
        json={
            "request_text": "What is the policy for sepsis treatment?",
            "user_id": "test_user",
        },
        timeout=10,
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    # Wait for completion (with timeout)
    max_wait = 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        status = status_data.get("status")
        
        if status in ["completed", "failed", "abstained"]:
            break
        
        time.sleep(2)
    
    # Verify final status
    final_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
    assert final_response.status_code == 200
    final_data = final_response.json()
    
    assert final_data["status"] in ["completed", "abstained"]
    if final_data["status"] == "completed":
        assert "final_answer" in final_data
        assert final_data["final_answer"] is not None


@pytest.mark.integration
def test_api_health(api_url):
    """Test API health endpoint."""
    response = requests.get(f"{api_url}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.integration
def test_metrics_endpoint(api_url):
    """Test metrics endpoint."""
    response = requests.get(f"{api_url}/metrics", timeout=5)
    assert response.status_code == 200
    assert "agent_runs_total" in response.text


@pytest.mark.integration
def test_tools_endpoint(api_url):
    """Test tools listing endpoint."""
    response = requests.get(f"{api_url}/tools", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 0

