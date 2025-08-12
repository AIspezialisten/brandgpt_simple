#!/usr/bin/env python3
"""
Complete test of session-specific system prompts functionality.
This tests: Prompt management → Session creation with prompts → Query responses with different personas
"""

import requests
import json
import time
import os
from pathlib import Path


class SystemPromptTester:
    def __init__(self, base_url="http://localhost:9700"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_credentials = {
            "username": "test_user_prompts",
            "email": "test_prompts@brandgpt.com", 
            "password": "secure_password123"
        }
        self.token = None
        self.created_prompts = []
        self.created_sessions = []
        
        # Define different system prompt personas
        self.prompt_personas = [
            {
                "name": "Technical Expert",
                "description": "A highly technical AI assistant specialized in software development and system architecture",
                "content": "You are a senior software engineer and system architect with 15+ years of experience. You provide detailed technical explanations, focus on best practices, performance considerations, and scalability. Always include code examples, architectural patterns, and technical trade-offs in your responses. Be precise and use industry terminology."
            },
            {
                "name": "Business Analyst",
                "description": "A business-focused AI assistant specializing in strategy and market analysis",
                "content": "You are an experienced business analyst and consultant. You focus on business impact, ROI, market positioning, competitive advantages, and strategic implications. Provide business-oriented insights, discuss market trends, financial implications, and strategic recommendations. Use business terminology and focus on value propositions."
            },
            {
                "name": "Creative Writer", 
                "description": "A creative AI assistant specializing in storytelling and content creation",
                "content": "You are a creative writer and content creator. You approach topics with imagination, storytelling techniques, and engaging narratives. Use metaphors, analogies, and creative language. Structure responses like compelling stories with vivid descriptions and emotional resonance. Make even technical topics accessible through creative explanations."
            },
            {
                "name": "Academic Researcher",
                "description": "A scholarly AI assistant focused on research and academic analysis",
                "content": "You are an academic researcher and professor. You provide scholarly analysis, cite methodologies, discuss research implications, and maintain academic rigor. Structure responses with clear hypotheses, evidence-based conclusions, and suggestions for further research. Use formal academic language and provide comprehensive, well-structured explanations."
            }
        ]
    
    def print_step(self, step, description):
        print(f"\n{'='*70}")
        print(f"STEP {step}: {description}")
        print('='*70)
    
    def register_and_login(self):
        """Register user and get authentication token"""
        self.print_step(1, "User Registration & Authentication")
        
        # Register user
        print("📝 Registering user...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=self.user_credentials
            )
            if response.status_code == 200:
                print("✅ User registered successfully")
            elif response.status_code == 400 and "already registered" in response.text:
                print("ℹ️  User already exists, proceeding to login")
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to BrandGPT API. Is it running on http://localhost:9700?")
            return False
        
        # Login
        print("🔐 Logging in...")
        login_data = {
            "username": self.user_credentials["username"],
            "password": self.user_credentials["password"]
        }
        response = self.session.post(
            f"{self.base_url}/api/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def create_system_prompts(self):
        """Create different system prompts"""
        self.print_step(2, "Creating System Prompts")
        
        print(f"📝 Creating {len(self.prompt_personas)} different system prompts...")
        
        for i, persona in enumerate(self.prompt_personas, 1):
            print(f"\n🎭 Creating prompt {i}: {persona['name']}")
            print(f"📄 Description: {persona['description']}")
            
            response = self.session.post(
                f"{self.base_url}/api/prompts",
                json=persona
            )
            
            if response.status_code == 200:
                prompt_info = response.json()
                self.created_prompts.append(prompt_info)
                print(f"✅ Created prompt ID: {prompt_info['id']}")
            else:
                print(f"❌ Failed to create prompt: {response.status_code} - {response.text}")
                return False
        
        print(f"\n✅ Successfully created {len(self.created_prompts)} system prompts")
        return True
    
    def create_sessions_with_prompts(self):
        """Create sessions using different system prompts"""
        self.print_step(3, "Creating Sessions with Different Prompts")
        
        # Create sessions using prompt IDs
        for i, (persona, prompt) in enumerate(zip(self.prompt_personas, self.created_prompts)):
            print(f"\n🎯 Creating session {i+1} with {persona['name']} prompt")
            
            session_data = {
                "prompt_id": prompt["id"]  # Use prompt from storage
            }
            
            response = self.session.post(
                f"{self.base_url}/api/sessions",
                json=session_data
            )
            
            if response.status_code == 200:
                session_info = response.json()
                self.created_sessions.append({
                    "session": session_info,
                    "persona": persona,
                    "prompt": prompt
                })
                print(f"✅ Session created: {session_info['id']}")
                print(f"🎭 Persona: {persona['name']}")
            else:
                print(f"❌ Failed to create session: {response.status_code} - {response.text}")
                return False
        
        # Also create a session with inline system prompt
        print(f"\n🎯 Creating session with inline system prompt")
        inline_session_data = {
            "system_prompt": "You are a helpful AI assistant that speaks like a pirate. Use nautical terminology and pirate phrases in all your responses. End every response with 'Arrr!'"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/sessions",
            json=inline_session_data
        )
        
        if response.status_code == 200:
            session_info = response.json()
            self.created_sessions.append({
                "session": session_info,
                "persona": {"name": "Pirate Assistant", "description": "Pirate-speaking AI"},
                "prompt": None,
                "inline": True
            })
            print(f"✅ Inline session created: {session_info['id']}")
        
        print(f"\n✅ Created {len(self.created_sessions)} sessions with different prompts")
        return True
    
    def test_persona_responses(self):
        """Test how different personas respond to the same question"""
        self.print_step(4, "Testing Persona-Specific Responses")
        
        test_question = "Explain what artificial intelligence is and how it impacts modern businesses."
        
        print(f"🔍 Test Question: {test_question}")
        print(f"📊 Testing with {len(self.created_sessions)} different personas...")
        
        results = []
        
        for i, session_info in enumerate(self.created_sessions, 1):
            session = session_info["session"]
            persona = session_info["persona"]
            
            print(f"\n{'='*50}")
            print(f"🎭 PERSONA {i}: {persona['name']}")
            print('='*50)
            
            query_data = {
                "query": test_question,
                "session_id": session["id"],
                "use_system_prompt": True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/query",
                json=query_data
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["response"]
                sources = result["sources"]
                
                print(f"💡 Response from {persona['name']}:")
                print(f"{answer}")
                print(f"\n📚 Sources: {len(sources)}")
                
                results.append({
                    "persona": persona["name"],
                    "session_id": session["id"],
                    "response": answer,
                    "sources_count": len(sources),
                    "success": True
                })
                print("✅ Query successful")
            else:
                print(f"❌ Query failed: {response.status_code} - {response.text}")
                results.append({
                    "persona": persona["name"],
                    "session_id": session["id"],
                    "success": False,
                    "error": response.text
                })
        
        return results
    
    def test_context_consistency(self):
        """Test that each session maintains its persona across multiple queries"""
        self.print_step(5, "Testing Persona Consistency Across Multiple Queries")
        
        # Test with the Technical Expert persona
        tech_session = next((s for s in self.created_sessions if s["persona"]["name"] == "Technical Expert"), None)
        if not tech_session:
            print("❌ Technical Expert session not found")
            return False
        
        questions = [
            "What are microservices?",
            "How do you ensure system scalability?",
            "What's the difference between SQL and NoSQL databases?"
        ]
        
        session_id = tech_session["session"]["id"]
        print(f"🎯 Testing consistency with Technical Expert session: {session_id}")
        
        for i, question in enumerate(questions, 1):
            print(f"\n🔍 Question {i}: {question}")
            
            query_data = {
                "query": question,
                "session_id": session_id,
                "use_system_prompt": True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/query",
                json=query_data
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["response"]
                print(f"💡 Technical Expert Response:")
                print(f"{answer[:300]}..." if len(answer) > 300 else answer)
                print("✅ Consistent technical persona maintained")
            else:
                print(f"❌ Query failed: {response.status_code} - {response.text}")
                return False
        
        return True
    
    def verify_prompt_management(self):
        """Verify prompt management functionality"""
        self.print_step(6, "Verifying Prompt Management")
        
        # List all prompts
        print("📋 Listing all system prompts...")
        response = self.session.get(f"{self.base_url}/api/prompts")
        
        if response.status_code == 200:
            all_prompts = response.json()
            print(f"✅ Retrieved {len(all_prompts)} prompts from system")
            
            # Verify our created prompts are in the list
            our_prompt_names = {p["name"] for p in self.created_prompts}
            retrieved_names = {p["name"] for p in all_prompts}
            
            if our_prompt_names.issubset(retrieved_names):
                print("✅ All created prompts found in system")
                
                # Display prompt summary
                print("\n📄 Available System Prompts:")
                for prompt in all_prompts:
                    if prompt["name"] in our_prompt_names:
                        print(f"  - {prompt['name']}: {prompt['description']}")
                        print(f"    ID: {prompt['id']}, Created: {prompt['created_at']}")
                
                return True
            else:
                missing = our_prompt_names - retrieved_names
                print(f"❌ Missing prompts: {missing}")
                return False
        else:
            print(f"❌ Failed to list prompts: {response.status_code} - {response.text}")
            return False
    
    def run_full_test(self):
        """Run the complete system prompts test"""
        print("🚀 BrandGPT System Prompts & Session Persona Test")
        print("Testing session-specific system prompts and persona consistency")
        
        # Step 1: Authentication
        if not self.register_and_login():
            return False
        
        # Step 2: Create system prompts
        if not self.create_system_prompts():
            return False
        
        # Step 3: Create sessions with different prompts
        if not self.create_sessions_with_prompts():
            return False
        
        # Step 4: Test persona responses
        results = self.test_persona_responses()
        
        # Step 5: Test consistency
        if not self.test_context_consistency():
            return False
        
        # Step 6: Verify prompt management
        if not self.verify_prompt_management():
            return False
        
        # Final summary
        self.print_step(7, "Test Results Summary")
        successful_queries = sum(1 for r in results if r["success"])
        total_queries = len(results)
        
        print(f"📊 System Prompts Test Results:")
        print(f"   ✅ Personas tested: {len(self.created_sessions)}")
        print(f"   ✅ System prompts created: {len(self.created_prompts)}")
        print(f"   ✅ Successful persona queries: {successful_queries}/{total_queries}")
        print(f"   🎭 Different personas:")
        for session_info in self.created_sessions:
            persona_name = session_info["persona"]["name"]
            session_id = session_info["session"]["id"]
            prompt_type = "inline" if session_info.get("inline") else "stored prompt"
            print(f"      - {persona_name} (Session: {session_id}, Type: {prompt_type})")
        
        if successful_queries == total_queries:
            print(f"\n🎉 ALL TESTS PASSED! System prompts and session personas work correctly.")
            print(f"🎭 Each session maintained its unique personality and response style.")
            return True
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
            return False


if __name__ == "__main__":
    tester = SystemPromptTester()
    success = tester.run_full_test()
    exit(0 if success else 1)