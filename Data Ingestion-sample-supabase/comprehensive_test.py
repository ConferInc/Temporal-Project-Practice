"""
Comprehensive test suite for versioned data platform.
Tests all functionality and reports bugs.
"""

import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000/api"

def log(message, level="INFO"):
    """Log messages."""
    print(f"[{level}] {message}")

def test_user_creation():
    """Test 1: Create a user."""
    log("TEST 1: Create User", "TEST")
    
    # Use unique email to avoid conflicts
    email = f"test.{int(time.time())}@example.com"
    payload = {
        "user": {
            "email": email,
            "organization_id": str(uuid.uuid4())
        }
    }
    
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    data = response.json()
    
    if data.get("success") and len(data.get("results", [])) > 0:
        user_id = data["results"][0].get("record_id")
        log(f"PASS: User created with ID: {user_id}", "PASS")
        return user_id
    else:
        log(f"FAIL: {data}", "FAIL")
        return None

def test_income_v1(user_id):
    """Test 2: Create income (version 1)."""
    log("TEST 2: Create Income v1", "TEST")
    
    payload = {
        "income": {
            "customer_id": user_id,
            "income_type": "salary",
            "monthly_amount": 50000
        }
    }
    
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    data = response.json()
    
    if data.get("success"):
        result = data["results"][0]
        version = result.get("version_number")
        is_update = result.get("is_update")
        
        if version == 1 and not is_update:
            log(f"PASS: Income v1 created", "PASS")
            return True
        else:
            log(f"FAIL: Expected v1, is_update=False, got v{version}, is_update={is_update}", "FAIL")
            return False
    else:
        log(f"FAIL: {data}", "FAIL")
        return False

def test_income_v2(user_id):
    """Test 3: Update income (version 2)."""
    log("TEST 3: Update Income v2", "TEST")
    
    payload = {
        "income": {
            "customer_id": user_id,
            "income_type": "salary",
            "monthly_amount": 65000
        }
    }
    
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    data = response.json()
    
    if data.get("success"):
        result = data["results"][0]
        version = result.get("version_number")
        is_update = result.get("is_update")
        
        if version == 2 and is_update:
            log(f"PASS: Income v2 created (versioning works!)", "PASS")
            return True
        else:
            log(f"FAIL: Expected v2, is_update=True, got v{version}, is_update={is_update}", "FAIL")
            return False
    else:
        log(f"FAIL: {data}", "FAIL")
        return False

def test_batch_insert(user_id):
    """Test 4: Batch insert multiple entities."""
    log("TEST 4: Batch Insert", "TEST")
    
    app_id = str(uuid.uuid4())
    payload = {
        "employment": {
            "customer_id": user_id,
            "employer_name": "Google Inc",
            "employment_type": "full_time"
        },
        "asset": {
            "customer_id": user_id,
            "application_id": app_id,
            "asset_type": "bank_account",
            "asset_value": 100000
        },
        "liability": {
            "customer_id": user_id,
            "application_id": app_id,
            "liability_type": "car_loan",
            "monthly_payment": 15000
        }
    }
    
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    data = response.json()
    
    if data.get("success") and data.get("total_processed") == 3:
        log(f"PASS: Batch insert successful (3 entities)", "PASS")
        return True
    else:
        log(f"FAIL: {data}", "FAIL")
        return False

def test_employment_update(user_id):
    """Test 5: Update employment (test versioning for employment)."""
    log("TEST 5: Update Employment", "TEST")
    
    payload = {
        "employment": {
            "customer_id": user_id,
            "employer_name": "Google Inc",
            "employment_type": "senior_full_time"
        }
    }
    
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    data = response.json()
    
    if data.get("success"):
        result = data["results"][0]
        version = result.get("version_number")
        is_update = result.get("is_update")
        
        if version == 2 and is_update:
            log(f"PASS: Employment v2 created", "PASS")
            return True
        else:
            log(f"FAIL: Expected v2, is_update=True, got v{version}, is_update={is_update}", "FAIL")
            return False
    else:
        log(f"FAIL: {data}", "FAIL")
        return False

def test_asset_update(user_id):
    """Test 6: Update asset (test versioning for assets)."""
    log("TEST 6: Update Asset", "TEST")
    
    payload = {
        "asset": {
            "customer_id": user_id,
            "asset_type": "bank_account",
            "asset_value": 150000
        }
    }
    
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    data = response.json()
    
    if data.get("success"):
        result = data["results"][0]
        version = result.get("version_number")
        is_update = result.get("is_update")
        
        if version == 2 and is_update:
            log(f"PASS: Asset v2 created", "PASS")
            return True
        else:
            log(f"FAIL: Expected v2, is_update=True, got v{version}, is_update={is_update}", "FAIL")
            return False
    else:
        log(f"FAIL: {data}", "FAIL")
        return False

def test_multiple_income_types(user_id):
    """Test 7: Multiple income types (different logical identity)."""
    log("TEST 7: Multiple Income Types", "TEST")
    
    payload = {
        "income": {
            "customer_id": user_id,
            "income_type": "bonus",
            "monthly_amount": 10000
        }
    }
    
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    data = response.json()
    
    if data.get("success"):
        result = data["results"][0]
        version = result.get("version_number")
        is_update = result.get("is_update")
        
        # This should be v1 because it's a different income_type
        if version == 1 and not is_update:
            log(f"PASS: Bonus income v1 created (separate from salary)", "PASS")
            return True
        else:
            log(f"FAIL: Expected v1, is_update=False, got v{version}, is_update={is_update}", "FAIL")
            return False
    else:
        log(f"FAIL: {data}", "FAIL")
        return False

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Test 1: Create user
    user_id = test_user_creation()
    if not user_id:
        log("Cannot continue - user creation failed", "ERROR")
        return
    
    print("-" * 60)
    time.sleep(0.5)
    
    # Test 2: Create income v1
    test_income_v1(user_id)
    print("-" * 60)
    time.sleep(0.5)
    
    # Test 3: Update income v2
    test_income_v2(user_id)
    print("-" * 60)
    time.sleep(0.5)
    
    # Test 4: Batch insert
    test_batch_insert(user_id)
    print("-" * 60)
    time.sleep(0.5)
    
    # Test 5: Update employment
    test_employment_update(user_id)
    print("-" * 60)
    time.sleep(0.5)
    
    # Test 6: Update asset
    test_asset_update(user_id)
    print("-" * 60)
    time.sleep(0.5)
    
    # Test 7: Multiple income types
    test_multiple_income_types(user_id)
    print("-" * 60)
    
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"Test User ID: {user_id}")
    print("Verify data in Supabase using this user ID")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
