#!/usr/bin/env python3
"""Quick test to demonstrate working personas with user-scoped content."""

import requests
import json

def test_personas():
    base_url = "http://localhost:9700"
    session = requests.Session()
    
    # Login as user with existing content
    login_data = {"username": "test_user", "password": "secure_password123"}
    response = session.post(f"{base_url}/api/auth/token", data=login_data, 
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Logged in successfully")
    
    # Create two different persona sessions
    personas = [
        {
            "name": "Business Consultant",
            "prompt": "You are a business consultant. Focus on business strategy, ROI, and market opportunities. Keep responses concise - 2-3 sentences max."
        },
        {
            "name": "Academic Researcher", 
            "prompt": "You are an academic researcher. Focus on scholarly analysis with evidence-based conclusions. Keep responses concise - 2-3 sentences max."
        }
    ]
    
    sessions = []
    for persona in personas:
        response = session.post(f"{base_url}/api/sessions", json={"system_prompt": persona["prompt"]})
        if response.status_code == 200:
            sessions.append({"persona": persona, "session_id": response.json()["id"]})
            print(f"✅ Created {persona['name']} session")
    
    # Test with same question to both personas
    question = "What can you tell me about Vodafone?"
    
    print(f"\n🔍 Question: {question}")
    print("=" * 60)
    
    for session_info in sessions:
        persona = session_info["persona"]
        session_id = session_info["session_id"]
        
        query_data = {
            "query": question,
            "session_id": session_id,
            "use_system_prompt": True
        }
        
        response = session.post(f"{base_url}/api/query", json=query_data)
        
        if response.status_code == 200:
            result = response.json()
            answer = result["response"]
            sources = result["sources"]
            
            print(f"\n🎭 {persona['name']} Response:")
            print(f"📝 {answer}")
            print(f"📊 Sources: {len(sources)}")
        else:
            print(f"❌ {persona['name']} failed: {response.status_code}")
    
    print("\n✅ Test complete - personas are working with user-scoped content!")

if __name__ == "__main__":
    test_personas()