#!/usr/bin/env python3
"""
Comprehensive test suite for v1 API backward compatibility features.
Tests dual authentication, structured data ingestion, and group-based filtering.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:9700"


class TestV1Compatibility:
    def __init__(self):
        self.base_url = BASE_URL
        self.jwt_token = None
        self.api_key = None
        self.user_id = None
        self.session_id = None
        
    def run_all_tests(self):
        """Run all v1 compatibility tests."""
        print("=" * 60)
        print("🧪 TESTING V1 API BACKWARD COMPATIBILITY")
        print("=" * 60)
        
        # Test 1: Dual Authentication
        if not self.test_dual_authentication():
            print("❌ Authentication tests failed")
            return False
            
        # Test 2: Structured Data Ingestion
        if not self.test_structured_data_ingestion():
            print("❌ Structured data ingestion tests failed")
            return False
            
        # Test 3: Group-based Filtering
        if not self.test_group_filtering():
            print("❌ Group filtering tests failed")
            return False
            
        print("\n" + "=" * 60)
        print("✅ ALL V1 COMPATIBILITY TESTS PASSED!")
        print("=" * 60)
        return True
    
    def test_dual_authentication(self):
        """Test both JWT and API key authentication."""
        print("\n📋 TEST 1: DUAL AUTHENTICATION")
        print("-" * 40)
        
        # Step 1: Register a new user
        print("1. Registering new user...")
        timestamp = int(time.time())
        user_data = {
            "username": f"v1_test_{timestamp}",
            "email": f"v1_test_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        if response.status_code != 200:
            print(f"   ❌ Registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        print("   ✅ User registered successfully")
        
        # Step 2: Test JWT authentication
        print("\n2. Testing JWT authentication...")
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        response = requests.post(
            f"{self.base_url}/api/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ JWT login failed: {response.status_code}")
            return False
            
        self.jwt_token = response.json()["access_token"]
        print(f"   ✅ JWT token obtained: {self.jwt_token[:20]}...")
        
        # Step 3: Generate API key
        print("\n3. Generating API key...")
        response = requests.post(
            f"{self.base_url}/api/auth/api-key",
            headers={"Authorization": f"Bearer {self.jwt_token}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ API key generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
        api_key_data = response.json()
        self.api_key = api_key_data["api_key"]
        print(f"   ✅ API key generated: {self.api_key[:20]}...")
        
        # Step 4: Test /api/auth/me with JWT
        print("\n4. Testing /api/auth/me with JWT...")
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers={"Authorization": f"Bearer {self.jwt_token}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ JWT auth test failed: {response.status_code}")
            return False
            
        user_info = response.json()
        self.user_id = user_info["id"]
        print(f"   ✅ JWT authentication works - User ID: {self.user_id}")
        
        # Step 5: Test /api/auth/me with API key
        print("\n5. Testing /api/auth/me with API key...")
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ API key auth test failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
        api_user_info = response.json()
        if api_user_info["id"] != self.user_id:
            print(f"   ❌ API key returned different user!")
            return False
            
        print(f"   ✅ API key authentication works - Same user ID: {api_user_info['id']}")
        
        # Step 6: Test API key without Bearer prefix
        print("\n6. Testing API key without Bearer prefix...")
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers={"Authorization": self.api_key}
        )
        
        if response.status_code != 200:
            print(f"   ❌ API key (no Bearer) failed: {response.status_code}")
            return False
            
        print("   ✅ API key works without Bearer prefix")
        
        print("\n🎯 DUAL AUTHENTICATION TEST PASSED!")
        return True
    
    def test_structured_data_ingestion(self):
        """Test structured data ingestion endpoint."""
        print("\n📋 TEST 2: STRUCTURED DATA INGESTION")
        print("-" * 40)
        
        # Create a session first (optional)
        print("1. Creating session (optional)...")
        session_data = {"system_prompt": "You are a helpful assistant."}
        response = requests.post(
            f"{self.base_url}/api/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code == 200:
            self.session_id = response.json()["id"]
            print(f"   ✅ Session created: {self.session_id}")
        else:
            print("   ℹ️  Proceeding without session (user-scoped)")
        
        # Test 1: Single object ingestion
        print("\n2. Testing single object ingestion...")
        single_object = {
            "data": {
                "id": 1,
                "name": "Test Product A",
                "price": 99.99,
                "category": "Electronics",
                "description": "High-quality wireless headphones with noise cancellation"
            },
            "group_id": "products_test",
            "metadata": {
                "source": "test_suite",
                "version": "1.0"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/ingest/structured",
            json=single_object,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Single object ingestion failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
        result = response.json()
        print(f"   ✅ Single object ingested - Document ID: {result['document_id']}")
        print(f"      Items processed: {result['items_processed']}")
        
        # Test 2: Array of objects ingestion
        print("\n3. Testing array of objects ingestion...")
        array_data = {
            "data": [
                {
                    "id": 2,
                    "name": "Test Product B",
                    "price": 149.99,
                    "category": "Electronics"
                },
                {
                    "id": 3,
                    "name": "Test Product C",
                    "price": 79.99,
                    "category": "Accessories"
                },
                {
                    "id": 4,
                    "name": "Test Product D",
                    "price": 199.99,
                    "category": "Electronics"
                }
            ],
            "group_id": "products_array_test",
            "session_id": self.session_id if self.session_id else None
        }
        
        response = requests.post(
            f"{self.base_url}/api/ingest/structured",
            json=array_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Array ingestion failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
        result = response.json()
        print(f"   ✅ Array ingested - Document ID: {result['document_id']}")
        print(f"      Items processed: {result['items_processed']}")
        
        if result['items_processed'] != 3:
            print(f"   ❌ Expected 3 items, got {result['items_processed']}")
            return False
        
        # Test 3: Complex nested structure
        print("\n4. Testing complex nested structure...")
        complex_data = {
            "data": {
                "company": "TechCorp",
                "departments": [
                    {
                        "name": "Engineering",
                        "employees": 50,
                        "projects": ["AI Platform", "Data Pipeline"]
                    },
                    {
                        "name": "Sales",
                        "employees": 30,
                        "regions": ["North America", "Europe", "Asia"]
                    }
                ],
                "metrics": {
                    "revenue": 1000000,
                    "growth": 0.25,
                    "customers": 500
                }
            },
            "group_id": "company_data"
        }
        
        response = requests.post(
            f"{self.base_url}/api/ingest/structured",
            json=complex_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Complex structure ingestion failed: {response.status_code}")
            return False
            
        print(f"   ✅ Complex nested structure ingested successfully")
        
        # Wait for processing
        print("\n5. Waiting for background processing...")
        time.sleep(3)
        
        print("\n🎯 STRUCTURED DATA INGESTION TEST PASSED!")
        return True
    
    def test_group_filtering(self):
        """Test group-based filtering in queries."""
        print("\n📋 TEST 3: GROUP-BASED FILTERING")
        print("-" * 40)
        
        # First, let's query without group filter
        print("1. Querying WITHOUT group filter...")
        query_data = {
            "query": "What products are available?",
            "use_system_prompt": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/query",
            json=query_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Query failed: {response.status_code}")
            return False
            
        result = response.json()
        sources_all = result.get("sources", [])
        print(f"   ✅ Query successful - Found {len(sources_all)} sources total")
        
        # Query with specific group_id
        print("\n2. Querying WITH group_id='products_test'...")
        query_data = {
            "query": "What products are available?",
            "group_id": "products_test",
            "use_system_prompt": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/query",
            json=query_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Group-filtered query failed: {response.status_code}")
            return False
            
        result = response.json()
        sources_filtered = result.get("sources", [])
        print(f"   ✅ Group filter applied - Found {len(sources_filtered)} sources")
        
        # Verify filtering worked
        if sources_filtered:
            for source in sources_filtered[:2]:
                metadata = source.get("metadata", {})
                group = metadata.get("group_id", "none")
                print(f"      Source group_id: {group}")
                if group != "products_test":
                    print(f"   ❌ Found source with wrong group_id: {group}")
                    return False
        
        # Query with different group_id
        print("\n3. Querying with group_id='products_array_test'...")
        query_data = {
            "query": "List all products with prices",
            "group_id": "products_array_test",
            "use_system_prompt": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/query",
            json=query_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Array group query failed: {response.status_code}")
            return False
            
        result = response.json()
        sources_array = result.get("sources", [])
        response_text = result.get("response", "")
        
        print(f"   ✅ Found {len(sources_array)} sources from array group")
        if response_text:
            print(f"   📝 Response preview: {response_text[:150]}...")
        
        # Query company data
        print("\n4. Querying complex structure with group_id='company_data'...")
        query_data = {
            "query": "How many employees are in Engineering department?",
            "group_id": "company_data",
            "use_system_prompt": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/query",
            json=query_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Company data query failed: {response.status_code}")
            return False
            
        result = response.json()
        response_text = result.get("response", "")
        
        if "50" in response_text or "fifty" in response_text.lower():
            print(f"   ✅ Correctly retrieved nested data (50 employees)")
        else:
            print(f"   ⚠️  Response may not contain expected data")
            print(f"      Response: {response_text[:200]}...")
        
        # Test non-existent group
        print("\n5. Testing query with non-existent group...")
        query_data = {
            "query": "What products are available?",
            "group_id": "nonexistent_group_xyz",
            "use_system_prompt": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/query",
            json=query_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Query with non-existent group failed: {response.status_code}")
            return False
            
        result = response.json()
        sources_none = result.get("sources", [])
        print(f"   ✅ Query successful - Found {len(sources_none)} sources (should be 0 or few)")
        
        print("\n🎯 GROUP-BASED FILTERING TEST PASSED!")
        return True


def main():
    """Run all v1 compatibility tests."""
    tester = TestV1Compatibility()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()