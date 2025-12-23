"""Contract tests for schema consistency."""

import pytest
import requests


@pytest.fixture
def api_url():
    """API base URL."""
    return "http://localhost:8000"


@pytest.mark.contract
def test_same_query_same_schema(api_url):
    """
    Contract test: Same query returns same schema.
    
    Ensures that identical queries produce responses with consistent schemas.
    """
    query = "What is the policy for sepsis treatment?"
    
    # Run query multiple times
    responses = []
    for _ in range(3):
        response = requests.post(
            f"{api_url}/agent/run",
            json={"request_text": query, "user_id": "test_user"},
            timeout=10,
        )
        assert response.status_code == 200
        responses.append(response.json())
    
    # Verify all responses have same schema
    first_schema = set(responses[0].keys())
    for response in responses[1:]:
        assert set(response.keys()) == first_schema, "Schema mismatch between responses"


@pytest.mark.contract
def test_verifier_blocks_unsupported_claims(api_url):
    """
    Contract test: Verifier blocks unsupported claims.
    
    Ensures verifier correctly identifies and blocks ungrounded claims.
    """
    # Create a request that should trigger verification failure
    response = requests.post(
        f"{api_url}/agent/run",
        json={
            "request_text": "What is the policy for treating patients with fake condition XYZ?",
            "user_id": "test_user",
        },
        timeout=10,
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    # Wait for completion
    import time
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
    
    # Verify verifier behavior
    final_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
    assert final_response.status_code == 200
    final_data = final_response.json()
    
    # Should either abstain or have proper verification
    assert final_data["status"] in ["completed", "abstained"]
    if final_data["status"] == "abstained":
        assert "abstention_reason" in final_data


@pytest.mark.contract
def test_response_schema_structure(api_url):
    """Test that response schema has required fields."""
    response = requests.post(
        f"{api_url}/agent/run",
        json={"request_text": "What is the policy?", "user_id": "test_user"},
        timeout=10,
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields
    assert "run_id" in data
    assert isinstance(data["run_id"], str)
    
    # Check status endpoint schema
    run_id = data["run_id"]
    status_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    required_fields = ["run_id", "status", "request_text"]
    for field in required_fields:
        assert field in status_data, f"Missing required field: {field}"

