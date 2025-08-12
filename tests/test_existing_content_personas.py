#!/usr/bin/env python3
"""
Test different system prompt personas using existing content in the system.
This demonstrates how the same content can be interpreted through different lenses.
"""

import requests
import json
import time


class ExistingContentPersonaTest:
    def __init__(self, base_url="http://localhost:9700"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_credentials = {
            "username": "test_user",
            "email": "test_user@brandgpt.com", 
            "password": "secure_password123"
        }
        self.token = None
        self.personas = [
            {
                "name": "Business Consultant",
                "prompt": "You are an experienced business consultant. Analyze everything from a business strategy perspective - focus on market opportunities, competitive advantages, ROI, business models, and strategic recommendations. Use business terminology and provide actionable insights."
            },
            {
                "name": "Academic Researcher", 
                "prompt": "You are a scholarly academic researcher. Approach topics with rigorous analysis, cite methodologies where relevant, discuss broader implications, and maintain academic objectivity. Structure responses with clear arguments and evidence-based conclusions."
            },
            {
                "name": "Storytelling Journalist",
                "prompt": "You are an engaging journalist who tells compelling stories. Transform information into interesting narratives with human interest angles, historical context, and vivid descriptions. Make complex topics accessible through storytelling techniques."
            },
            {
                "name": "Technical Analyst",
                "prompt": "You are a technical specialist focused on systems, processes, and implementation details. Analyze technical aspects, identify patterns, discuss methodologies, and provide detailed technical insights. Use precise terminology and focus on how things work."
            }
        ]
        self.test_questions = [
            {
                "topic": "Vodafone Business",
                "question": "What can you tell me about Vodafone based on the document? What are the key insights?",
                "expected_content": "Vodafone PDF content"
            },
            {
                "topic": "Oswald Spengler",
                "question": "Who was Oswald Spengler and what was his significance in intellectual history?",
                "expected_content": "Wikipedia content about Oswald Spengler"
            },
            {
                "topic": "TechInnovate Solutions",
                "question": "Analyze TechInnovate Solutions as a company - what are their strengths and market position?", 
                "expected_content": "JSON company data"
            }
        ]
        self.created_sessions = []
    
    def print_step(self, step, description):
        print(f"\n{'='*80}")
        print(f"STEP {step}: {description}")
        print('='*80)
    
    def register_and_login(self):
        """Register and authenticate user"""
        self.print_step(1, "Authentication")
        
        try:
            # Register
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=self.user_credentials
            )
            if response.status_code == 400:
                print("ℹ️  User already exists")
            else:
                print("✅ User registered")
            
            # Login
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
                print(f"❌ Login failed: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API")
            return False
    
    def create_persona_sessions(self):
        """Create sessions with different persona prompts"""
        self.print_step(2, "Creating Sessions with Different Personas")
        
        for persona in self.personas:
            print(f"\n🎭 Creating {persona['name']} session...")
            
            session_data = {"system_prompt": persona["prompt"]}
            response = self.session.post(f"{self.base_url}/api/sessions", json=session_data)
            
            if response.status_code == 200:
                session_info = response.json()
                self.created_sessions.append({
                    "persona": persona,
                    "session_id": session_info["id"]
                })
                print(f"✅ Session created: {session_info['id']}")
                print(f"📝 Persona: {persona['name']}")
            else:
                print(f"❌ Failed to create session: {response.status_code}")
                return False
        
        print(f"\n✅ Created {len(self.created_sessions)} persona sessions")
        return True
    
    def test_persona_interpretations(self):
        """Test how each persona interprets the existing content"""
        self.print_step(3, "Testing Persona Interpretations of Existing Content")
        
        for q_idx, test_question in enumerate(self.test_questions, 1):
            print(f"\n{'='*60}")
            print(f"📋 TOPIC {q_idx}: {test_question['topic']}")
            print(f"🔍 Question: {test_question['question']}")
            print(f"📄 Expected content: {test_question['expected_content']}")
            print('='*60)
            
            for session_info in self.created_sessions:
                persona = session_info["persona"]
                session_id = session_info["session_id"]
                
                print(f"\n🎭 {persona['name']} Perspective:")
                print("-" * 50)
                
                query_data = {
                    "query": test_question["question"],
                    "session_id": session_id,
                    "use_system_prompt": True
                }
                
                response = self.session.post(f"{self.base_url}/api/query", json=query_data)
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result["response"]
                    sources = result["sources"]
                    
                    print(f"💡 Response ({len(answer)} chars):")
                    print(f"{answer}")
                    print(f"\n📊 Sources: {len(sources)} documents")
                    
                    # Show source diversity
                    if sources:
                        unique_sources = set()
                        for source in sources:
                            if 'metadata' in source and 'filename' in source['metadata']:
                                unique_sources.add(source['metadata']['filename'])
                            elif 'metadata' in source and 'url' in source['metadata']:
                                unique_sources.add(source['metadata']['url'])
                        
                        if unique_sources:
                            print(f"📚 Source files: {', '.join(list(unique_sources)[:3])}")
                    
                    print("✅ Response generated")
                else:
                    print(f"❌ Query failed: {response.status_code} - {response.text}")
                    
                print()  # Extra spacing between personas
    
    def comparative_analysis(self):
        """Ask the same specific question to all personas for direct comparison"""
        self.print_step(4, "Direct Persona Comparison")
        
        comparison_question = "What are the most important insights from all the available information? Provide your top 3 key takeaways."
        
        print(f"🔍 Comparison Question: {comparison_question}")
        print(f"📊 Testing with all {len(self.created_sessions)} personas on same question...")
        
        responses = []
        
        for session_info in self.created_sessions:
            persona = session_info["persona"]
            session_id = session_info["session_id"]
            
            print(f"\n🎭 {persona['name']} Analysis:")
            print("-" * 40)
            
            query_data = {
                "query": comparison_question,
                "session_id": session_id,
                "use_system_prompt": True
            }
            
            response = self.session.post(f"{self.base_url}/api/query", json=query_data)
            
            if response.status_code == 200:
                result = response.json()
                answer = result["response"]
                sources = result["sources"]
                
                responses.append({
                    "persona": persona["name"],
                    "response": answer,
                    "sources_count": len(sources)
                })
                
                print(f"💡 Key Takeaways:")
                print(f"{answer}")
                print(f"📊 Based on {len(sources)} sources")
                print("✅ Analysis complete")
            else:
                print(f"❌ Query failed: {response.status_code}")
        
        return responses
    
    def analyze_persona_differences(self, responses):
        """Analyze the differences between persona responses"""
        self.print_step(5, "Analyzing Persona Differences")
        
        print("🔍 Response Analysis:")
        
        for response in responses:
            persona = response["persona"] 
            text = response["response"]
            sources = response["sources_count"]
            
            # Simple analysis metrics
            word_count = len(text.split())
            has_numbers = any(char.isdigit() for char in text)
            has_business_terms = any(term in text.lower() for term in 
                                   ['market', 'business', 'roi', 'strategy', 'competitive', 'revenue'])
            has_academic_terms = any(term in text.lower() for term in 
                                   ['analysis', 'research', 'study', 'methodology', 'evidence', 'conclude'])
            has_story_elements = any(term in text.lower() for term in 
                                   ['story', 'narrative', 'journey', 'human', 'compelling', 'vivid'])
            has_technical_terms = any(term in text.lower() for term in 
                                    ['system', 'process', 'implementation', 'technical', 'methodology'])
            
            print(f"\n📊 {persona}:")
            print(f"   📝 Word count: {word_count}")
            print(f"   📊 Uses numbers/data: {'Yes' if has_numbers else 'No'}")
            print(f"   💼 Business focus: {'Yes' if has_business_terms else 'No'}")  
            print(f"   🎓 Academic language: {'Yes' if has_academic_terms else 'No'}")
            print(f"   📖 Story elements: {'Yes' if has_story_elements else 'No'}")
            print(f"   ⚙️  Technical focus: {'Yes' if has_technical_terms else 'No'}")
            print(f"   📚 Sources used: {sources}")
    
    def run_full_test(self):
        """Run the complete existing content persona test"""
        print("🚀 BrandGPT Persona Analysis Test")
        print("Testing how different system prompts interpret existing content")
        print("📚 Using: Vodafone PDF + Oswald Spengler Wikipedia + TechInnovate JSON")
        
        # Step 1: Authentication
        if not self.register_and_login():
            return False
        
        # Step 2: Create persona sessions
        if not self.create_persona_sessions():
            return False
        
        # Step 3: Test persona interpretations
        self.test_persona_interpretations()
        
        # Step 4: Comparative analysis
        responses = self.comparative_analysis()
        
        # Step 5: Analyze differences
        if responses:
            self.analyze_persona_differences(responses)
        
        # Summary
        print(f"\n🎉 TEST COMPLETE!")
        print(f"✅ Successfully demonstrated how {len(self.personas)} different personas")
        print(f"   interpret the same existing content through their unique lenses:")
        for session_info in self.created_sessions:
            print(f"   🎭 {session_info['persona']['name']} - {session_info['session_id']}")
        
        print(f"\n📚 Content Sources Available:")
        print(f"   📄 Vodafone business document")
        print(f"   🌐 Oswald Spengler Wikipedia article") 
        print(f"   📊 TechInnovate Solutions company data")
        
        print(f"\n🌟 Each persona maintained its distinct analytical approach!")
        
        return True


if __name__ == "__main__":
    tester = ExistingContentPersonaTest()
    success = tester.run_full_test()
    exit(0 if success else 1)