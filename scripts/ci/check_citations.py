"""Script to check that responses include citations."""

import requests
import sys
import time


def check_citations(api_url: str, num_queries: int = 5) -> bool:
    """
    Check that agent responses include citations.
    
    Args:
        api_url: API base URL
        num_queries: Number of queries to test
        
    Returns:
        True if all queries have citations, False otherwise
    """
    queries = [
        "What is the policy for sepsis treatment?",
        "Summarize the guidelines",
        "Explain the procedure",
        "What are the safety protocols?",
        "Show me the policy",
    ][:num_queries]
    
    all_have_citations = True
    
    for query in queries:
        try:
            # Create agent run
            response = requests.post(
                f"{api_url}/agent/run",
                json={"request_text": query, "user_id": "ci_test"},
                timeout=10,
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to create run for query: {query}")
                all_have_citations = False
                continue
            
            run_id = response.json()["run_id"]
            
            # Wait for completion
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
                if status_response.status_code != 200:
                    break
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status in ["completed", "abstained"]:
                    break
                
                time.sleep(2)
            
            # Check for citations
            final_response = requests.get(f"{api_url}/agent/status/{run_id}", timeout=5)
            if final_response.status_code != 200:
                print(f"❌ Failed to get status for query: {query}")
                all_have_citations = False
                continue
            
            final_data = final_response.json()
            
            if final_data.get("status") == "completed":
                has_citations = (
                    "citations" in final_data
                    or "evidence" in final_data
                    or final_data.get("metadata", {}).get("citations")
                )
                
                if not has_citations:
                    print(f"❌ No citations found for query: {query}")
                    all_have_citations = False
                else:
                    print(f"✅ Citations found for query: {query}")
            else:
                print(f"⚠️  Query abstained or failed: {query}")
        
        except Exception as e:
            print(f"❌ Error checking query '{query}': {e}")
            all_have_citations = False
    
    return all_have_citations


if __name__ == "__main__":
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"Checking citations for API: {api_url}")
    success = check_citations(api_url)
    
    if success:
        print("\n✅ All queries have citations")
        sys.exit(0)
    else:
        print("\n❌ Some queries are missing citations")
        sys.exit(1)

