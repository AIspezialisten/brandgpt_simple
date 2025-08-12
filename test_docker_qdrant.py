#!/usr/bin/env python3
"""Test Qdrant connectivity and vector operations from the Docker deployment."""

import requests
import json
import time

def test_docker_qdrant_integration():
    base_url = "http://localhost:9700"
    
    print("🔗 Testing Docker Qdrant Integration")
    print("=" * 45)
    
    # First login to get token
    user_data = {
        "username": "docker_test_user", 
        "email": "docker_test@example.com",
        "password": "testpass123"
    }
    
    # Register user (ignore if exists)
    requests.post(f"{base_url}/api/auth/register", json=user_data)
    
    # Login
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    response = requests.post(
        f"{base_url}/api/auth/token", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print("❌ Failed to authenticate")
        return False
        
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Authentication successful")
    
    # Create a session
    print("1. Creating session...")
    session_data = {"system_prompt": "You are a helpful assistant."}
    response = requests.post(f"{base_url}/api/sessions", json=session_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code}")
        return False
        
    session_id = response.json()["id"]
    print(f"   ✅ Session created: {session_id}")
    
    # Test text ingestion (this will test Qdrant connectivity)
    print("2. Testing text ingestion to Qdrant...")
    
    # Create a test text file
    import tempfile
    import os
    
    test_content = """
    This is a test document for Docker deployment testing.
    It contains information about artificial intelligence and machine learning.
    The purpose is to verify that the RAG pipeline works correctly in containers.
    Vector embeddings should be stored in Qdrant successfully.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        # Upload the file
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_docker.txt', f, 'text/plain')}
            response = requests.post(
                f"{base_url}/api/ingest/file/{session_id}",
                files=files,
                headers=headers
            )
        
        if response.status_code != 200:
            print(f"❌ File ingestion failed: {response.status_code}")
            print(response.text)
            return False
            
        document_id = response.json()["document_id"]
        print(f"   ✅ File ingestion started: document_id={document_id}")
        
        # Wait for processing
        print("3. Waiting for document processing...")
        time.sleep(8)  # Give it time to process and store in Qdrant
        
        # Test query (this will test vector search in Qdrant)
        print("4. Testing vector search query...")
        query_data = {
            "query": "What is artificial intelligence?",
            "session_id": session_id,
            "use_system_prompt": True
        }
        
        response = requests.post(f"{base_url}/api/query", json=query_data, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Query failed: {response.status_code}")
            print(response.text)
            return False
            
        result = response.json()
        answer = result["response"]
        sources = result["sources"]
        
        print(f"   ✅ Query successful:")
        print(f"      📝 Response: {answer[:100]}..." if len(answer) > 100 else f"      📝 Response: {answer}")
        print(f"      📊 Sources found: {len(sources)}")
        
        if len(sources) > 0:
            print(f"      🎯 Vector search working - found relevant documents")
            return True
        else:
            print(f"      ⚠️  No sources found - vector search may not be working")
            return False
            
    finally:
        # Cleanup
        os.unlink(temp_file_path)

if __name__ == "__main__":
    success = test_docker_qdrant_integration()
    if success:
        print("\n🎉 Docker Qdrant integration test PASSED!")
        print("   • API can reach Qdrant ✅")
        print("   • Vector storage working ✅") 
        print("   • Vector search working ✅")
        print("   • Full RAG pipeline functional ✅")
    else:
        print("\n❌ Docker Qdrant integration test FAILED!")
        print("Check docker-compose logs for details")
    
    exit(0 if success else 1)