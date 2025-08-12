#!/usr/bin/env python3
"""Quick test of Docker deployment functionality."""

import requests
import time

def test_docker_deployment():
    base_url = "http://localhost:9700"
    
    print("🧪 Testing Docker Deployment")
    print("=" * 40)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200 and response.json().get("status") == "healthy":
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test user registration
    print("2. Testing user registration...")
    user_data = {
        "username": "docker_test_user",
        "email": "docker_test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=user_data, timeout=10)
        if response.status_code in [200, 400]:  # 400 if user exists
            print("   ✅ Registration endpoint working")
        else:
            print(f"   ❌ Registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False
    
    # Test login
    print("3. Testing authentication...")
    try:
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        response = requests.post(
            f"{base_url}/api/auth/token", 
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                print("   ✅ Authentication working")
                
                # Test authenticated endpoint
                print("4. Testing authenticated endpoint...")
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"{base_url}/api/sessions", headers=headers, timeout=10)
                if response.status_code == 200:
                    print("   ✅ Authenticated endpoints working")
                else:
                    print(f"   ❌ Authenticated endpoint failed: {response.status_code}")
                    return False
            else:
                print("   ❌ No token received")
                return False
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False
    
    print("\n🎉 Docker deployment test successful!")
    print("All core functionality is working in the containerized environment.")
    return True

if __name__ == "__main__":
    # Wait a moment for services to be fully ready
    print("⏳ Waiting for services to be fully ready...")
    time.sleep(3)
    
    success = test_docker_deployment()
    exit(0 if success else 1)