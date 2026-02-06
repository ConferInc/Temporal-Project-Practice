import requests
import json

# Test 1: Create user
print("Testing user creation...")
payload = {
    "user": {
        "email": "test@example.com",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000"
    }
}

response = requests.post("http://localhost:8000/api/ingest", json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
