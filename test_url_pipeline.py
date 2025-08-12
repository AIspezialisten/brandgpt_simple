#!/usr/bin/env python3
"""
Complete end-to-end test of the RAG pipeline using URL ingestion.
This tests: URL scraping → Content extraction → Vector storage → Query → Response generation
"""

import requests
import json
import time
import os
from pathlib import Path


class BrandGPTURLTester:
    def __init__(self, base_url="http://localhost:9700"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_credentials = {
            "username": "test_user_url",
            "email": "test_url@brandgpt.com",
            "password": "secure_password123"
        }
        self.token = None
        self.session_id = None
        self.document_id = None
        self.test_url = "https://de.wikipedia.org/wiki/Oswald_Spengler"
    
    def print_step(self, step, description):
        print(f"\n{'='*60}")
        print(f"STEP {step}: {description}")
        print('='*60)
    
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
    
    def create_session(self):
        """Create a new RAG session"""
        self.print_step(2, "Creating RAG Session")
        
        session_data = {
            "system_prompt": "You are a helpful AI assistant specialized in analyzing web content and biographical information. "
                           "Provide detailed and accurate answers based on the scraped web content."
        }
        
        response = self.session.post(
            f"{self.base_url}/api/sessions",
            json=session_data
        )
        
        if response.status_code == 200:
            session_info = response.json()
            self.session_id = session_info["id"]
            print(f"✅ Session created: {self.session_id}")
            print(f"📝 System prompt: {session_data['system_prompt'][:60]}...")
            return True
        else:
            print(f"❌ Session creation failed: {response.status_code} - {response.text}")
            return False
    
    def ingest_url(self):
        """Ingest the Wikipedia URL"""
        self.print_step(3, "URL Content Ingestion")
        
        print(f"🌐 Processing URL: {self.test_url}")
        print("📄 Target: Oswald Spengler Wikipedia page (German)")
        
        url_data = {
            "url": self.test_url,
            "session_id": self.session_id,
            "content_type": "url",
            "max_depth": 1  # Only scrape the main page
        }
        
        response = self.session.post(
            f"{self.base_url}/api/ingest/url",
            json=url_data
        )
        
        if response.status_code == 200:
            result = response.json()
            self.document_id = result["document_id"]
            print(f"✅ URL ingestion started")
            print(f"📄 Document ID: {self.document_id}")
            print(f"⏳ Status: {result['status']}")
            return True
        else:
            print(f"❌ URL ingestion failed: {response.status_code} - {response.text}")
            return False
    
    def wait_for_processing(self, max_wait_seconds=120):
        """Wait for document processing to complete"""
        self.print_step(4, "Waiting for URL Processing")
        
        print("⏳ Waiting for URL scraping and processing to complete...")
        print("📊 Note: URL processing may take longer than file uploads")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            response = self.session.get(f"{self.base_url}/api/documents/{self.session_id}")
            
            if response.status_code == 200:
                documents = response.json()
                doc = next((d for d in documents if d["id"] == self.document_id), None)
                
                if doc:
                    status = doc["processed"]
                    print(f"📊 Processing status: {status}")
                    
                    if status == "completed":
                        print("✅ URL processing completed successfully")
                        return True
                    elif status == "failed":
                        error = doc.get("error_message", "Unknown error")
                        print(f"❌ URL processing failed: {error}")
                        return False
                else:
                    print("⚠️  Document not found in session")
            
            time.sleep(5)  # Check every 5 seconds for URL processing
        
        print(f"⏰ Processing timeout after {max_wait_seconds} seconds")
        return False
    
    def show_scraped_content(self):
        """Display scraped content chunks"""
        self.print_step("4.5", "Scraped Content Preview")
        
        # Make a simple query to get some content chunks
        query_data = {
            "query": "show me content from this webpage",
            "session_id": self.session_id,
            "use_system_prompt": False
        }
        
        response = self.session.post(
            f"{self.base_url}/api/query",
            json=query_data
        )
        
        if response.status_code == 200:
            result = response.json()
            sources = result["sources"]
            
            print(f"🌐 Website content was scraped and chunked. Here are some examples:")
            print(f"📊 Total chunks retrieved for preview: {len(sources)}")
            
            for i, source in enumerate(sources[:5]):  # Show first 5 chunks
                print(f"\n📄 Chunk {i+1}:")
                content = source.get('text', '')
                print(f"   Content: {content[:400]}{'...' if len(content) > 400 else ''}")
                if 'metadata' in source:
                    metadata = source['metadata']
                    print(f"   Source URL: {metadata.get('url', 'N/A')}")
                    print(f"   Title: {metadata.get('title', 'N/A')}")
            
            if len(sources) > 5:
                print(f"\n... and {len(sources) - 5} more chunks")
        else:
            print(f"❌ Could not retrieve scraped content: {response.status_code} - {response.text}")
    
    def test_queries(self):
        """Test various queries against the scraped content"""
        self.print_step(5, "Testing Queries on Scraped Content")
        
        test_queries = [
            {
                "query": "Who was Oswald Spengler and what was he known for? Provide a detailed biographical overview.",
                "description": "Biographical overview"
            },
            {
                "query": "What is 'Der Untergang des Abendlandes' (The Decline of the West) and what are its main themes?",
                "description": "Main work analysis"
            },
            {
                "query": "What were Oswald Spengler's key philosophical ideas and theories about history and civilization?",
                "description": "Philosophical theories"
            },
            {
                "query": "When and where was Oswald Spengler born and when did he die? What were the key dates in his life?",
                "description": "Biographical timeline"
            },
            {
                "query": "What influence did Oswald Spengler have on later thinkers and intellectual movements?",
                "description": "Influence and legacy"
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n🔍 Query {i}: {test['description']}")
            print(f"❓ Question: {test['query']}")
            
            query_data = {
                "query": test["query"],
                "session_id": self.session_id,
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
                
                print(f"💡 Full Answer:\n{answer}")
                print(f"\n📚 Sources found: {len(sources)}")
                
                if sources:
                    for j, source in enumerate(sources):  # Show all sources
                        print(f"\n   📄 Source {j+1}:")
                        content = source.get('text', '')
                        print(f"      Text: {content[:200]}{'...' if len(content) > 200 else ''}")
                        print(f"      Score: {source.get('score', 'N/A')}")
                        if 'metadata' in source:
                            metadata = source['metadata']
                            print(f"      URL: {metadata.get('url', 'N/A')}")
                            print(f"      Title: {metadata.get('title', 'N/A')}")
                
                results.append({
                    "query": test["query"],
                    "answer": answer,
                    "sources_count": len(sources),
                    "success": True
                })
                print("✅ Query successful")
            else:
                print(f"❌ Query failed: {response.status_code} - {response.text}")
                results.append({
                    "query": test["query"],
                    "success": False,
                    "error": response.text
                })
        
        return results
    
    def run_full_test(self):
        """Run the complete end-to-end URL ingestion test"""
        print("🚀 BrandGPT End-to-End URL Ingestion Pipeline Test")
        print(f"Testing with: {self.test_url}")
        
        # Step 1: Authentication
        if not self.register_and_login():
            return False
        
        # Step 2: Create session
        if not self.create_session():
            return False
        
        # Step 3: Ingest URL
        if not self.ingest_url():
            return False
        
        # Step 4: Wait for processing
        if not self.wait_for_processing():
            return False
        
        # Step 4.5: Show scraped content
        self.show_scraped_content()
        
        # Step 5: Test queries
        results = self.test_queries()
        
        # Final summary
        self.print_step(6, "Test Results Summary")
        successful_queries = sum(1 for r in results if r["success"])
        total_queries = len(results)
        
        print(f"📊 Test Results:")
        print(f"   ✅ Successful queries: {successful_queries}/{total_queries}")
        print(f"   🌐 URL processed: {self.test_url}")
        print(f"   🔗 Session ID: {self.session_id}")
        print(f"   📄 Document ID: {self.document_id}")
        
        if successful_queries == total_queries:
            print(f"\n🎉 ALL TESTS PASSED! The URL ingestion pipeline is working correctly.")
            return True
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
            return False


if __name__ == "__main__":
    tester = BrandGPTURLTester()
    success = tester.run_full_test()
    exit(0 if success else 1)