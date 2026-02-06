"""
Quick test script to verify the API is working.
Run this while the server is running to test the health endpoint.
"""

import requests

def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        response = requests.get("http://localhost:8000/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ingest_endpoint():
    """Test the ingest endpoint with sample data."""
    payload = {
        "data": {
            "income": {
                "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                "income_type": "salary",
                "monthly_amount": 50000
            }
        }
    }
    
    try:
        response = requests.post("http://localhost:8000/api/ingest", json=payload)
        print(f"\nIngest Test:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Versioned Data Platform API...\n")
    print("=" * 50)
    
    health_ok = test_health_endpoint()
    
    print("\n" + "=" * 50)
    print(f"\nHealth Check: {'✓ PASSED' if health_ok else '✗ FAILED'}")
    
    # Uncomment to test ingestion (requires Supabase to be configured)
    # ingest_ok = test_ingest_endpoint()
    # print(f"Ingestion Test: {'✓ PASSED' if ingest_ok else '✗ FAILED'}")
