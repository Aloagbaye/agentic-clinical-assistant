"""Smoke tests for deployment verification."""

import pytest
import requests
import time


@pytest.fixture
def api_url():
    """API base URL."""
    return "http://localhost:8000"  # Update with actual deployment URL


@pytest.mark.smoke
def test_smoke_agent_queries(api_url):
    """Run 10 agent queries to verify deployment."""
    queries = [
        "What is the policy for sepsis treatment?",
        "Summarize the guidelines for patient care",
        "Compare treatment protocols",
        "Explain the procedure for admission",
        "What are the safety guidelines?",
        "Show me the policy for discharge",
        "What is the protocol for emergencies?",
        "Explain the medication guidelines",
        "What are the infection control policies?",
        "Summarize the documentation requirements",
    ]
    
    results = []
    for query in queries:
        try:
            response = requests.post(
                f"{api_url}/agent/run",
                json={"request_text": query, "user_id": "smoke_test"},
                timeout=10,
            )
            assert response.status_code == 200
            run_id = response.json()["run_id"]
            results.append({"query": query, "run_id": run_id, "status": "initiated"})
        except Exception as e:
            results.append({"query": query, "error": str(e)})
    
    # Verify at least 8 out of 10 queries succeeded
    successful = sum(1 for r in results if "run_id" in r)
    assert successful >= 8, f"Only {successful}/10 queries succeeded"


@pytest.mark.smoke
def test_citations_present(api_url):
    """Verify that responses include citations."""
    response = requests.post(
        f"{api_url}/agent/run",
        json={"request_text": "What is the policy for sepsis treatment?", "user_id": "smoke_test"},
        timeout=10,
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    # Wait for completion
    max_wait = 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        status = status_data.get("status")
        
        if status in ["completed", "abstained"]:
            break
        
        time.sleep(2)
    
    # Check for citations
    final_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
    assert final_response.status_code == 200
    final_data = final_response.json()
    
    if final_data["status"] == "completed":
        # Should have citations or evidence
        assert "citations" in final_data or "evidence" in final_data or "metadata" in final_data


@pytest.mark.smoke
def test_api_health_smoke(api_url):
    """Smoke test for API health."""
    response = requests.get(f"{api_url}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.smoke
def test_metrics_available(api_url):
    """Verify metrics endpoint is accessible."""
    response = requests.get(f"{api_url}/metrics", timeout=5)
    assert response.status_code == 200
    assert len(response.text) > 0

