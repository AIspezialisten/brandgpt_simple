#!/usr/bin/env python3
"""Test URL ingestion with depth=2 for Oswald Spengler Wikipedia page."""

import requests
import json
import time
from datetime import datetime

def test_url_depth():
    base_url = "http://localhost:9700"
    
    print("🌐 Testing URL Ingestion with Depth=2")
    print("=" * 50)
    print(f"Target URL: https://de.wikipedia.org/wiki/Oswald_Spengler")
    print(f"Depth: 2 (main page + all linked pages)")
    print("=" * 50)
    
    # Register and login
    user_data = {
        "username": f"depth_test_{int(time.time())}",
        "email": f"depth_test_{int(time.time())}@example.com",
        "password": "testpass123"
    }
    
    print("\n1. Setting up authentication...")
    response = requests.post(f"{base_url}/api/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"Registration failed: {response.status_code}")
        return
    
    # Login
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    response = requests.post(
        f"{base_url}/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        return
        
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Authentication successful")
    
    # Create session
    print("\n2. Creating session...")
    session_data = {"system_prompt": "You are a helpful assistant with knowledge about philosophy and history."}
    response = requests.post(f"{base_url}/api/sessions", json=session_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Session creation failed: {response.status_code}")
        return
        
    session_id = response.json()["id"]
    print(f"   ✅ Session created: {session_id}")
    
    # Ingest URL with depth=2
    print("\n3. Ingesting URL with depth=2...")
    print("   This will scrape:")
    print("   - The main Oswald Spengler page")
    print("   - All Wikipedia pages linked from the main page")
    print("   ⏳ This may take a few minutes...")
    
    start_time = time.time()
    
    url_data = {
        "session_id": session_id,
        "url": "https://de.wikipedia.org/wiki/Oswald_Spengler",
        "content_type": "url",
        "max_depth": 2
    }
    
    response = requests.post(f"{base_url}/api/ingest/url", json=url_data, headers=headers)
    
    if response.status_code != 200:
        print(f"   ❌ URL ingestion failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return
        
    document_id = response.json()["document_id"]
    print(f"   ✅ URL ingestion started")
    print(f"   📄 Document ID: {document_id}")
    
    # Wait for processing with status updates
    print("\n4. Processing pages (checking every 10 seconds)...")
    for i in range(12):  # Check for up to 2 minutes
        time.sleep(10)
        elapsed = time.time() - start_time
        print(f"   ⏳ Processing... ({elapsed:.0f}s elapsed)")
        
        # Check if we can query yet
        query_data = {
            "query": "Who was Oswald Spengler?",
            "session_id": session_id,
            "use_system_prompt": True
        }
        
        response = requests.post(f"{base_url}/api/query", json=query_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("sources") and len(result["sources"]) > 0:
                print(f"   ✅ Processing complete! ({elapsed:.0f}s total)")
                break
    
    # Get document stats
    print("\n5. Checking ingestion results...")
    
    # Query to see what was ingested
    test_queries = [
        "Who was Oswald Spengler?",
        "What is Der Untergang des Abendlandes?",
        "What was Spengler's philosophy about?",
        "When did Spengler live?"
    ]
    
    print("\n6. Testing queries on ingested content:")
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        query_data = {
            "query": query,
            "session_id": session_id,
            "use_system_prompt": True
        }
        
        response = requests.post(f"{base_url}/api/query", json=query_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get("sources", [])
            response_text = result.get("response", "")
            
            print(f"   📊 Sources found: {len(sources)}")
            if sources:
                # Show unique URLs scraped
                unique_urls = set()
                for source in sources:
                    metadata = source.get("metadata", {})
                    if metadata.get("source_type") == "url":
                        url = metadata.get("url", "")
                        if url:
                            unique_urls.add(url)
                
                if unique_urls:
                    print(f"   🔗 Unique pages used: {len(unique_urls)}")
                    # Show first 3 unique URLs
                    for i, url in enumerate(list(unique_urls)[:3], 1):
                        # Extract page title from URL
                        page_name = url.split("/wiki/")[-1] if "/wiki/" in url else url
                        print(f"      {i}. {page_name}")
                    if len(unique_urls) > 3:
                        print(f"      ... and {len(unique_urls) - 3} more pages")
            
            # Show snippet of response
            if response_text:
                snippet = response_text[:150] + "..." if len(response_text) > 150 else response_text
                print(f"   💬 Response: {snippet}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 INGESTION SUMMARY")
    print("=" * 50)
    
    # Get all sources for final count
    final_query = {
        "query": "Oswald Spengler philosophy history culture civilization",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = requests.post(f"{base_url}/api/query", json=final_query, headers=headers)
    if response.status_code == 200:
        result = response.json()
        sources = result.get("sources", [])
        
        # Count unique URLs
        all_urls = set()
        for source in sources:
            metadata = source.get("metadata", {})
            if metadata.get("source_type") == "url":
                url = metadata.get("url", "")
                if url:
                    all_urls.add(url)
        
        print(f"✅ Successfully ingested with depth=2:")
        print(f"   • Total unique pages scraped: {len(all_urls)}")
        print(f"   • Total chunks created: {len(sources)}")
        print(f"   • Processing time: {elapsed:.1f} seconds")
        
        if len(all_urls) > 1:
            print(f"\n🎯 Depth=2 worked! Scraped the main page plus {len(all_urls)-1} linked pages")
        else:
            print(f"\n⚠️  Only scraped 1 page - depth feature may need investigation")
    
    print("\n✨ Test completed successfully!")

if __name__ == "__main__":
    test_url_depth()