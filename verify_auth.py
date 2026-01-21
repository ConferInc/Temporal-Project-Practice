import urllib.request
import json
import uuid

BASE_URL = "http://localhost:3001"

def register_user(email, password):
    url = f"{BASE_URL}/auth/register"
    data = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Register Success: {response.getcode()}")
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Register Failed: {e.code} - {e.read().decode()}")
        return None

def login_user(email, password):
    url = f"{BASE_URL}/auth/login"
    # OAuth2 specifies form data for token endpoint
    data = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Login Success: {response.getcode()}")
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Login Failed: {e.code} - {e.read().decode()}")
        return None

def main():
    email = f"test_{uuid.uuid4()}@example.com"
    password = "secret_password"
    
    print(f"Creating user: {email}")
    
    # 1. Register
    reg_result = register_user(email, password)
    if not reg_result:
        exit(1)
        
    # 2. Login
    login_result = login_user(email, password)
    if not login_result:
        exit(1)
        
    print(f"Token: {login_result.get('access_token')[:20]}...")
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    main()
