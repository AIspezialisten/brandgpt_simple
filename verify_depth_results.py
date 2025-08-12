#!/usr/bin/env python3
"""Verify the depth parameter results by checking what was actually scraped."""

import requests
import time

def verify_depth_results():
    base_url = "http://localhost:9700"
    
    # Use same authentication from previous test
    user = {
        "username": f"verify_test_{int(time.time())}",
        "email": f"verify_test_{int(time.time())}@test.com",
        "password": "testpass123"
    }
    
    # Quick auth
    requests.post(f"{base_url}/api/auth/register", json=user)
    resp = requests.post(
        f"{base_url}/api/auth/token",
        data={"username": user["username"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create session
    session_resp = requests.post(
        f"{base_url}/api/sessions",
        json={"system_prompt": "You are a helpful assistant."},
        headers=headers
    )
    session_id = session_resp.json()["id"]
    
    print("🔍 Verifying Depth Parameter Results")
    print("=" * 45)
    
    # Test with small depth first
    print("Testing depth=1 vs depth=2 comparison...")
    
    # Test depth=1
    print("\n1. Testing depth=1 (only main page)...")
    depth1_data = {
        "session_id": session_id,
        "url": "https://de.wikipedia.org/wiki/Oswald_Spengler",
        "content_type": "url", 
        "max_depth": 1
    }
    
    start_time = time.time()
    resp1 = requests.post(f"{base_url}/api/ingest/url", json=depth1_data, headers=headers)
    doc_id_1 = resp1.json()["document_id"]
    
    # Wait and query
    time.sleep(15)
    query_resp_1 = requests.post(
        f"{base_url}/api/query",
        json={"query": "Oswald Spengler Der Untergang des Abendlandes", "session_id": session_id},
        headers=headers
    )
    
    if query_resp_1.status_code == 200:
        result1 = query_resp_1.json()
        sources1 = result1.get("sources", [])
        
        unique_urls_1 = set()
        for source in sources1:
            url = source.get("metadata", {}).get("url", "")
            if url:
                unique_urls_1.add(url)
        
        print(f"   📊 Depth=1 results:")
        print(f"      • Chunks: {len(sources1)}")
        print(f"      • Unique pages: {len(unique_urls_1)}")
        for url in list(unique_urls_1)[:3]:
            page = url.split('/wiki/')[-1] if '/wiki/' in url else url
            print(f"         - {page}")
    
    # Now test depth=2 with a DIFFERENT session to avoid mixing results
    print("\n2. Testing depth=2 (main page + links)...")
    
    # Create new session for clean comparison
    session2_resp = requests.post(
        f"{base_url}/api/sessions",
        json={"system_prompt": "You are a helpful assistant."},
        headers=headers
    )
    session_id_2 = session2_resp.json()["id"]
    
    depth2_data = {
        "session_id": session_id_2,
        "url": "https://de.wikipedia.org/wiki/Oswald_Spengler",
        "content_type": "url",
        "max_depth": 2
    }
    
    resp2 = requests.post(f"{base_url}/api/ingest/url", json=depth2_data, headers=headers)
    doc_id_2 = resp2.json()["document_id"]
    
    # Wait longer for depth=2 processing
    time.sleep(25)
    query_resp_2 = requests.post(
        f"{base_url}/api/query",
        json={"query": "Oswald Spengler Der Untergang des Abendlandes", "session_id": session_id_2},
        headers=headers
    )
    
    if query_resp_2.status_code == 200:
        result2 = query_resp_2.json()
        sources2 = result2.get("sources", [])
        
        unique_urls_2 = set()
        for source in sources2:
            url = source.get("metadata", {}).get("url", "")
            if url:
                unique_urls_2.add(url)
        
        print(f"   📊 Depth=2 results:")
        print(f"      • Chunks: {len(sources2)}")
        print(f"      • Unique pages: {len(unique_urls_2)}")
        for url in list(unique_urls_2)[:5]:
            page = url.split('/wiki/')[-1] if '/wiki/' in url else url
            print(f"         - {page}")
        
        print(f"\n🎯 COMPARISON:")
        print(f"   • Depth=1: {len(unique_urls_1)} pages, {len(sources1)} chunks")
        print(f"   • Depth=2: {len(unique_urls_2)} pages, {len(sources2)} chunks")
        
        if len(unique_urls_2) > len(unique_urls_1):
            print(f"   ✅ SUCCESS: Depth=2 scraped {len(unique_urls_2) - len(unique_urls_1)} additional pages!")
            return True
        else:
            print(f"   ⚠️  Both depths scraped same number of unique pages")
            return False
    
    return False

if __name__ == "__main__":
    success = verify_depth_results()
    if success:
        print("\n🎉 Depth parameter is working correctly!")
    else:
        print("\n🤔 Need to investigate depth parameter implementation")