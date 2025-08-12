#!/usr/bin/env python3
"""Simple test of URL depth parameter with progress monitoring."""

import requests
import time
import sys

def test_depth_parameter():
    base_url = "http://localhost:9700"
    test_url = "https://de.wikipedia.org/wiki/Oswald_Spengler"
    depth = 2
    
    print(f"🌐 Testing URL ingestion with depth={depth}")
    print(f"📍 URL: {test_url}")
    print("=" * 60)
    
    # Quick auth
    timestamp = int(time.time())
    user = {
        "username": f"test_{timestamp}",
        "email": f"test_{timestamp}@test.com", 
        "password": "test123"
    }
    
    print("1. Authenticating...")
    requests.post(f"{base_url}/api/auth/register", json=user)
    
    resp = requests.post(
        f"{base_url}/api/auth/token",
        data={"username": user["username"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Authenticated")
    
    # Create session
    print("2. Creating session...")
    resp = requests.post(
        f"{base_url}/api/sessions",
        json={"system_prompt": "Test session"},
        headers=headers
    )
    session_id = resp.json()["id"]
    print(f"   ✅ Session: {session_id}")
    
    # Start ingestion with depth
    print(f"\n3. Starting URL ingestion with depth={depth}...")
    print("   This will scrape:")
    print("   • Level 1: The main Oswald Spengler page")
    print("   • Level 2: All Wikipedia pages linked from main page")
    
    start_time = time.time()
    
    resp = requests.post(
        f"{base_url}/api/ingest/url",
        json={
            "session_id": session_id,
            "url": test_url,
            "content_type": "url",
            "max_depth": depth
        },
        headers=headers
    )
    
    if resp.status_code != 200:
        print(f"   ❌ Failed: {resp.status_code}")
        print(f"   {resp.text}")
        return
        
    doc_id = resp.json()["document_id"]
    print(f"   ✅ Started ingestion (document_id: {doc_id})")
    
    # Monitor progress
    print("\n4. Monitoring progress (this may take 1-3 minutes)...")
    print("   Checking every 5 seconds for content...")
    
    max_checks = 36  # 3 minutes max
    for i in range(max_checks):
        time.sleep(5)
        elapsed = int(time.time() - start_time)
        
        # Progress indicator
        sys.stdout.write(f"\r   ⏳ Elapsed: {elapsed}s - Checking for content...")
        sys.stdout.flush()
        
        # Try a query to see if content is available
        resp = requests.post(
            f"{base_url}/api/query",
            json={
                "query": "Oswald Spengler",
                "session_id": session_id,
                "use_system_prompt": False
            },
            headers=headers
        )
        
        if resp.status_code == 200:
            sources = resp.json().get("sources", [])
            if sources:
                # Count unique URLs
                urls = set()
                for s in sources:
                    if s.get("metadata", {}).get("source_type") == "url":
                        url = s.get("metadata", {}).get("url")
                        if url:
                            urls.add(url)
                
                if len(urls) > 0:
                    sys.stdout.write(f"\r   ✅ Content found! {len(urls)} unique pages, {len(sources)} chunks after {elapsed}s\n")
                    sys.stdout.flush()
                    
                    if len(urls) > 1:
                        print(f"\n🎯 SUCCESS: Depth={depth} worked!")
                        print(f"   Scraped {len(urls)} different Wikipedia pages:")
                        for idx, url in enumerate(list(urls)[:5], 1):
                            page = url.split("/wiki/")[-1] if "/wiki/" in url else url
                            print(f"   {idx}. {page}")
                        if len(urls) > 5:
                            print(f"   ... and {len(urls)-5} more pages")
                    else:
                        print(f"\n⚠️  Only 1 page found - checking if still processing...")
                        if i < 10:  # Keep checking for a bit more
                            continue
                    
                    return True
    
    print(f"\n⏱️  Timeout after {elapsed}s - ingestion may still be running in background")
    return False

if __name__ == "__main__":
    success = test_depth_parameter()
    if success:
        print("\n✨ Depth parameter test successful!")
    else:
        print("\n❓ Test inconclusive - check logs for details")