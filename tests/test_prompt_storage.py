#!/usr/bin/env python3
"""Test prompt storage and retrieval functionality."""

import requests
import json

def test_prompt_storage():
    base_url = "http://localhost:9700"
    session = requests.Session()
    
    # Login as user
    login_data = {"username": "test_user", "password": "secure_password123"}
    response = session.post(f"{base_url}/api/auth/token", data=login_data, 
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Logged in successfully")
    
    # Create some example prompts
    example_prompts = [
        {
            "name": "Marketing Expert",
            "description": "AI persona focused on marketing strategy and brand positioning",
            "content": "You are a senior marketing strategist with 15+ years of experience. Focus on brand positioning, target audience analysis, marketing channels, campaign effectiveness, and ROI. Provide actionable marketing insights and recommendations."
        },
        {
            "name": "Data Scientist", 
            "description": "AI persona focused on data analysis and insights",
            "content": "You are a data scientist with expertise in statistical analysis, machine learning, and data visualization. Focus on data patterns, statistical significance, predictive insights, and data-driven recommendations. Use quantitative reasoning and mention relevant metrics."
        },
        {
            "name": "Creative Director",
            "description": "AI persona focused on creative and design thinking",
            "content": "You are a creative director with extensive experience in design, branding, and creative campaigns. Focus on visual appeal, brand storytelling, creative concepts, user experience, and innovative approaches. Think outside the box and suggest creative solutions."
        }
    ]
    
    print("\n📝 Creating and storing prompts...")
    created_prompts = []
    
    for prompt in example_prompts:
        response = session.post(f"{base_url}/api/prompts", json=prompt)
        
        if response.status_code == 200:
            created_prompt = response.json()
            created_prompts.append(created_prompt)
            print(f"✅ Created prompt: {prompt['name']} (ID: {created_prompt['id']})")
        else:
            print(f"❌ Failed to create prompt {prompt['name']}: {response.status_code}")
    
    # Retrieve all stored prompts
    print("\n📚 Retrieving all stored prompts...")
    response = session.get(f"{base_url}/api/prompts")
    
    if response.status_code == 200:
        all_prompts = response.json()
        print(f"✅ Retrieved {len(all_prompts)} prompts:")
        
        for prompt in all_prompts[-3:]:  # Show last 3 prompts
            print(f"  🎭 {prompt['name']}: {prompt['description']}")
            print(f"     ID: {prompt['id']}, Created: {prompt['created_at']}")
    else:
        print(f"❌ Failed to retrieve prompts: {response.status_code}")
    
    # Test using stored prompts in sessions
    if created_prompts:
        print("\n🎯 Testing prompt usage in sessions...")
        
        # Use the Marketing Expert prompt
        marketing_prompt = created_prompts[0]
        session_data = {"prompt_id": marketing_prompt["id"]}
        
        response = session.post(f"{base_url}/api/sessions", json=session_data)
        
        if response.status_code == 200:
            session_info = response.json()
            print(f"✅ Created session with stored prompt: {marketing_prompt['name']}")
            
            # Test query with this session
            query_data = {
                "query": "How can Vodafone improve their brand positioning?",
                "session_id": session_info["id"],
                "use_system_prompt": True
            }
            
            response = session.post(f"{base_url}/api/query", json=query_data)
            
            if response.status_code == 200:
                result = response.json()
                answer = result["response"]
                sources = result["sources"]
                
                print(f"🎭 Marketing Expert Response:")
                print(f"📝 {answer[:200]}..." if len(answer) > 200 else answer)
                print(f"📊 Sources: {len(sources)}")
            else:
                print(f"❌ Query failed: {response.status_code}")
        else:
            print(f"❌ Failed to create session with stored prompt: {response.status_code}")
    
    print("\n✅ Prompt storage and retrieval test complete!")
    print("\n📋 Summary of Available Endpoints:")
    print("  • POST /api/prompts - Store new prompts")
    print("  • GET /api/prompts - Retrieve all stored prompts")  
    print("  • POST /api/sessions - Create sessions with stored prompts using 'prompt_id'")
    print("  • POST /api/sessions - Create sessions with inline prompts using 'system_prompt'")

if __name__ == "__main__":
    test_prompt_storage()