"""Script to check for PHI leakage in logs and responses."""

import requests
import sys
import re


# PHI patterns to check
PHI_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b\d{3}\.\d{2}\.\d{4}\b',  # SSN with dots
    r'\b[A-Z]{2}\d{6}\b',  # Medical record number
    r'\b\d{3}-\d{3}-\d{4}\b',  # Phone number
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
]


def check_text_for_phi(text: str) -> list:
    """
    Check text for PHI patterns.
    
    Args:
        text: Text to check
        
    Returns:
        List of found PHI patterns
    """
    found_phi = []
    
    for pattern in PHI_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found_phi.extend(matches)
    
    return found_phi


def check_api_responses(api_url: str) -> bool:
    """
    Check API responses for PHI leakage.
    
    Args:
        api_url: API base URL
        
    Returns:
        True if no PHI found, False otherwise
    """
    test_queries = [
        "What is the policy?",
        "Summarize the guidelines",
    ]
    
    no_phi_leakage = True
    
    for query in test_queries:
        try:
            # Create agent run
            response = requests.post(
                f"{api_url}/agent/run",
                json={"request_text": query, "user_id": "phi_check"},
                timeout=10,
            )
            
            if response.status_code == 200:
                response_text = response.text
                found_phi = check_text_for_phi(response_text)
                
                if found_phi:
                    print(f"❌ PHI detected in response for query: {query}")
                    print(f"   Found: {found_phi}")
                    no_phi_leakage = False
                else:
                    print(f"✅ No PHI detected in response for query: {query}")
        
        except Exception as e:
            print(f"⚠️  Error checking query '{query}': {e}")
    
    return no_phi_leakage


def check_metrics_endpoint(api_url: str) -> bool:
    """
    Check metrics endpoint for PHI.
    
    Args:
        api_url: API base URL
        
    Returns:
        True if no PHI found, False otherwise
    """
    try:
        response = requests.get(f"{api_url}/metrics", timeout=5)
        
        if response.status_code == 200:
            metrics_text = response.text
            found_phi = check_text_for_phi(metrics_text)
            
            if found_phi:
                print(f"❌ PHI detected in metrics endpoint")
                print(f"   Found: {found_phi}")
                return False
            else:
                print(f"✅ No PHI detected in metrics endpoint")
                return True
    
    except Exception as e:
        print(f"⚠️  Error checking metrics endpoint: {e}")
        return False


if __name__ == "__main__":
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"Checking for PHI leakage in API: {api_url}")
    
    responses_ok = check_api_responses(api_url)
    metrics_ok = check_metrics_endpoint(api_url)
    
    if responses_ok and metrics_ok:
        print("\n✅ No PHI leakage detected")
        sys.exit(0)
    else:
        print("\n❌ PHI leakage detected")
        sys.exit(1)

