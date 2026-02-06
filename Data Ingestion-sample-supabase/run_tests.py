"""
Automated test script for the versioned data platform.
Tests all functionality and reports any bugs found.
"""

import requests
import json
import time
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

class TestRunner:
    def __init__(self):
        self.test_results = []
        self.user_id = None
        self.bugs_found = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_health_check(self) -> bool:
        """Test 1: Health check endpoint."""
        self.log("TEST 1: Health Check", "TEST")
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ Health check passed: {data}", "PASS")
                return True
            else:
                self.log(f"✗ Health check failed: {response.status_code}", "FAIL")
                self.bugs_found.append(f"Health check returned {response.status_code}")
                return False
        except Exception as e:
            self.log(f"✗ Health check error: {e}", "FAIL")
            self.bugs_found.append(f"Health check exception: {e}")
            return False
    
    def test_create_user(self) -> bool:
        """Test 2: Create a new user."""
        self.log("TEST 2: Create User", "TEST")
        payload = {
            "user": {
                "email": f"test.user.{int(time.time())}@example.com",
                "organization_id": "org-test-001"
            }
        }
        
        try:
            response = requests.post(f"{API_URL}/ingest", json=payload, timeout=10)
            self.log(f"Response status: {response.status_code}")
            self.log(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and len(data.get("results", [])) > 0:
                    result = data["results"][0]
                    self.user_id = result.get("record_id")
                    self.log(f"✓ User created: {self.user_id}", "PASS")
                    self.log(f"  Version: {result.get('version_number')}")
                    self.log(f"  Is Update: {result.get('is_update')}")
                    return True
                else:
                    self.log(f"✗ User creation failed: {data}", "FAIL")
                    self.bugs_found.append(f"User creation unsuccessful: {data}")
                    return False
            else:
                self.log(f"✗ User creation failed: {response.status_code}", "FAIL")
                self.bugs_found.append(f"User creation returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log(f"✗ User creation error: {e}", "FAIL")
            self.bugs_found.append(f"User creation exception: {e}")
            return False
    
    def test_create_income(self) -> bool:
        """Test 3: Create income record (version 1)."""
        if not self.user_id:
            self.log("✗ Skipping income test - no user ID", "SKIP")
            return False
            
        self.log("TEST 3: Create Income (Version 1)", "TEST")
        payload = {
            "income": {
                "customer_id": self.user_id,
                "income_type": "salary",
                "monthly_amount": 50000
            }
        }
        
        try:
            response = requests.post(f"{API_URL}/ingest", json=payload, timeout=10)
            self.log(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data["results"][0]
                    version = result.get("version_number")
                    is_update = result.get("is_update")
                    
                    if version == 1 and is_update == False:
                        self.log(f"✓ Income created: version {version}", "PASS")
                        return True
                    else:
                        self.log(f"✗ Unexpected version/update: v{version}, update={is_update}", "FAIL")
                        self.bugs_found.append(f"Income v1: Expected version=1, is_update=False, got version={version}, is_update={is_update}")
                        return False
                else:
                    self.log(f"✗ Income creation failed: {data}", "FAIL")
                    self.bugs_found.append(f"Income creation unsuccessful: {data}")
                    return False
            else:
                self.log(f"✗ Income creation failed: {response.status_code}", "FAIL")
                self.bugs_found.append(f"Income creation returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log(f"✗ Income creation error: {e}", "FAIL")
            self.bugs_found.append(f"Income creation exception: {e}")
            return False
    
    def test_update_income(self) -> bool:
        """Test 4: Update income record (version 2)."""
        if not self.user_id:
            self.log("✗ Skipping income update test - no user ID", "SKIP")
            return False
            
        self.log("TEST 4: Update Income (Version 2)", "TEST")
        payload = {
            "income": {
                "customer_id": self.user_id,
                "income_type": "salary",
                "monthly_amount": 65000
            }
        }
        
        try:
            response = requests.post(f"{API_URL}/ingest", json=payload, timeout=10)
            self.log(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data["results"][0]
                    version = result.get("version_number")
                    is_update = result.get("is_update")
                    
                    if version == 2 and is_update == True:
                        self.log(f"✓ Income updated: version {version}", "PASS")
                        return True
                    else:
                        self.log(f"✗ Unexpected version/update: v{version}, update={is_update}", "FAIL")
                        self.bugs_found.append(f"Income v2: Expected version=2, is_update=True, got version={version}, is_update={is_update}")
                        return False
                else:
                    self.log(f"✗ Income update failed: {data}", "FAIL")
                    self.bugs_found.append(f"Income update unsuccessful: {data}")
                    return False
            else:
                self.log(f"✗ Income update failed: {response.status_code}", "FAIL")
                self.bugs_found.append(f"Income update returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log(f"✗ Income update error: {e}", "FAIL")
            self.bugs_found.append(f"Income update exception: {e}")
            return False
    
    def test_batch_insert(self) -> bool:
        """Test 5: Batch insert multiple entities."""
        if not self.user_id:
            self.log("✗ Skipping batch test - no user ID", "SKIP")
            return False
            
        self.log("TEST 5: Batch Insert (Multiple Entities)", "TEST")
        payload = {
            "employment": {
                "customer_id": self.user_id,
                "employer_name": "Google Inc",
                "employment_type": "full_time"
            },
            "asset": {
                "customer_id": self.user_id,
                "application_id": "app-test-001",
                "asset_type": "bank_account",
                "asset_value": 100000
            },
            "liability": {
                "customer_id": self.user_id,
                "application_id": "app-test-001",
                "liability_type": "car_loan",
                "monthly_payment": 15000
            }
        }
        
        try:
            response = requests.post(f"{API_URL}/ingest", json=payload, timeout=10)
            self.log(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("total_processed") == 3:
                    self.log(f"✓ Batch insert successful: {data['total_processed']} entities", "PASS")
                    return True
                else:
                    self.log(f"✗ Batch insert failed: {data}", "FAIL")
                    self.bugs_found.append(f"Batch insert: Expected 3 entities, got {data.get('total_processed')}")
                    return False
            else:
                self.log(f"✗ Batch insert failed: {response.status_code}", "FAIL")
                self.bugs_found.append(f"Batch insert returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log(f"✗ Batch insert error: {e}", "FAIL")
            self.bugs_found.append(f"Batch insert exception: {e}")
            return False
    
    def test_invalid_entity(self) -> bool:
        """Test 6: Invalid entity type handling."""
        self.log("TEST 6: Invalid Entity Type Handling", "TEST")
        payload = {
            "invalid_entity": {
                "some_field": "some_value"
            }
        }
        
        try:
            response = requests.post(f"{API_URL}/ingest", json=payload, timeout=10)
            self.log(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("success") and len(data.get("errors", [])) > 0:
                    self.log(f"✓ Invalid entity properly rejected", "PASS")
                    return True
                else:
                    self.log(f"✗ Invalid entity not rejected: {data}", "FAIL")
                    self.bugs_found.append(f"Invalid entity should be rejected but wasn't")
                    return False
            else:
                self.log(f"Response status: {response.status_code}", "INFO")
                return True  # Error handling is acceptable
        except Exception as e:
            self.log(f"✗ Invalid entity test error: {e}", "FAIL")
            self.bugs_found.append(f"Invalid entity test exception: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report."""
        self.log("=" * 60)
        self.log("STARTING AUTOMATED TEST SUITE")
        self.log("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Create User", self.test_create_user),
            ("Create Income v1", self.test_create_income),
            ("Update Income v2", self.test_update_income),
            ("Batch Insert", self.test_batch_insert),
            ("Invalid Entity", self.test_invalid_entity),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"✗ Test '{test_name}' crashed: {e}", "ERROR")
                failed += 1
            
            self.log("-" * 60)
            time.sleep(0.5)  # Small delay between tests
        
        # Generate report
        self.log("=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"Total Tests: {len(tests)}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        self.log(f"Success Rate: {(passed/len(tests)*100):.1f}%")
        
        if self.bugs_found:
            self.log("=" * 60)
            self.log("BUGS FOUND", "ERROR")
            self.log("=" * 60)
            for i, bug in enumerate(self.bugs_found, 1):
                self.log(f"{i}. {bug}", "BUG")
        else:
            self.log("=" * 60)
            self.log("✓ NO BUGS FOUND - ALL TESTS PASSED!", "SUCCESS")
            self.log("=" * 60)
        
        if self.user_id:
            self.log("=" * 60)
            self.log(f"Test User ID: {self.user_id}")
            self.log("Use this ID to verify data in Supabase")
            self.log("=" * 60)

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
