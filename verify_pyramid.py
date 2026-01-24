import requests
import time
import uuid

BASE_URL = "http://localhost:3001"
EMAIL = f"test_ceo_{uuid.uuid4().hex[:6]}@example.com"
PWD = "password123"

def run():
    # 1. Register
    print(f"1. Registering {EMAIL}...")
    requests.post(f"{BASE_URL}/auth/register", json={"email": EMAIL, "password": PWD})

    # 2. Login
    print("2. Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": EMAIL, "password": PWD})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Apply with Pyramid Flag
    print("3. Submitting Loan (Pyramid Mode)...")
    # Using dummy files for test
    files = {
        'id_document': ('id.pdf', b'dummy content', 'application/pdf'),
        'tax_document': ('tax.pdf', b'dummy content', 'application/pdf'),
        'pay_stub': ('pay.pdf', b'dummy content', 'application/pdf'),
        'credit_document': ('credit.pdf', b'dummy content', 'application/pdf'),
    }
    data = {
        "name": "CEO Test",
        "email": EMAIL,
        "ssn": "123-45",
        "income": 90000,
        "use_pyramid": "true"  # <--- THIS IS KEY
    }
    
    apply_resp = requests.post(f"{BASE_URL}/apply", headers=headers, files=files, data=data)
    if apply_resp.status_code != 200:
        print(f"❌ Failed to apply: {apply_resp.text}")
        return
    
    app_id = apply_resp.json()["workflow_id"]
    print(f"✅ Loan Started! ID: {app_id}")

    # 4. Check Status
    print("4. Checking CEO Status...")
    time.sleep(2)
    state_resp = requests.get(f"{BASE_URL}/applications/{app_id}/history", headers=headers)
    
    print("\n--- CEO REPORT ---")
    print(state_resp.json())

if __name__ == "__main__":
    run()