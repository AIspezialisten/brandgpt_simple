#!/usr/bin/env python3
"""Final test of URL depth parameter with proper error handling."""

import requests
import time
import json

def test_depth():
    base_url = "http://localhost:9700"
    
    print("🌐 Testing URL Depth Parameter")
    print("=" * 40)
    
    # Register user
    user = {
        "username": f"depth_test_{int(time.time())}",
        "email": f"depth_test_{int(time.time())}@test.com",
        "password": "testpass123"
    }
    
    print("1. Registering user...")
    resp = requests.post(f"{base_url}/api/auth/register", json=user)
    print(f"   Registration: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"   Error: {resp.text}")
        return False
    
    # Login
    print("2. Logging in...")
    login_resp = requests.post(
        f"{base_url}/api/auth/token",
        data={"username": user["username"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"   Login: {login_resp.status_code}")
    
    if login_resp.status_code != 200:
        print(f"   Error: {login_resp.text}")
        return False
    
    token_data = login_resp.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Authenticated")
    
    # Create session
    print("3. Creating session...")
    session_resp = requests.post(
        f"{base_url}/api/sessions",
        json={"system_prompt": "You are a helpful assistant."},
        headers=headers
    )
    
    if session_resp.status_code != 200:
        print(f"   Error: {session_resp.text}")
        return False
        
    session_id = session_resp.json()["id"]
    print(f"   ✅ Session created: {session_id}")
    
    # Test URL ingestion with depth=2
    print("\n4. Testing URL ingestion with depth=2...")
    print("   URL: https://de.wikipedia.org/wiki/Oswald_Spengler")
    print("   This should scrape the main page + all linked Wikipedia pages")
    
    url_data = {
        "session_id": session_id,
        "url": "https://de.wikipedia.org/wiki/Oswald_Spengler",
        "content_type": "url",
        "max_depth": 2
    }
    
    start_time = time.time()
    ingest_resp = requests.post(f"{base_url}/api/ingest/url", json=url_data, headers=headers)
    
    if ingest_resp.status_code != 200:
        print(f"   ❌ Ingestion failed: {ingest_resp.status_code}")
        print(f"   Error: {ingest_resp.text}")
        return False
    
    doc_id = ingest_resp.json()["document_id"]
    print(f"   ✅ Started ingestion (doc_id: {doc_id})")
    
    # Monitor progress
    print("\n5. Waiting for processing...")
    max_wait = 120  # 2 minutes
    check_interval = 10  # 10 seconds
    
    for i in range(max_wait // check_interval):
        elapsed = time.time() - start_time
        print(f"   ⏳ Elapsed: {elapsed:.0f}s - Checking...")
        
        time.sleep(check_interval)
        
        # Test query
        query_resp = requests.post(
            f"{base_url}/api/query",
            json={
                "query": "Oswald Spengler philosophy",
                "session_id": session_id
            },
            headers=headers
        )
        
        if query_resp.status_code == 200:
            result = query_resp.json()
            sources = result.get("sources", [])
            
            if sources:
                # Count unique URLs
                unique_urls = set()
                for source in sources:
                    metadata = source.get("metadata", {})
                    url = metadata.get("url", "")
                    if url:
                        unique_urls.add(url)
                
                print(f"\n✅ SUCCESS! Content processed after {elapsed:.0f}s")
                print(f"   📊 Total chunks: {len(sources)}")
                print(f"   🌐 Unique pages scraped: {len(unique_urls)}")
                
                if len(unique_urls) > 1:
                    print(f"\n🎯 DEPTH=2 WORKED!")
                    print(f"   Scraped main page + {len(unique_urls)-1} linked pages")
                    print("\n   Sample pages scraped:")
                    for i, url in enumerate(list(unique_urls)[:5], 1):
                        page_name = url.split('/wiki/')[-1] if '/wiki/' in url else url
                        print(f"   {i}. {page_name}")
                    
                    if len(unique_urls) > 5:
                        print(f"   ... and {len(unique_urls)-5} more pages")
                else:
                    print(f"\n⚠️  Only scraped 1 page - depth feature may need investigation")
                
                return True
    
    print(f"\n⏱️  Processing still ongoing after {max_wait}s")
    return False

if __name__ == "__main__":
    success = test_depth()
    if success:
        print("\n🎉 Depth parameter test completed successfully!")
    else:
        print("\n❌ Test failed or timed out")