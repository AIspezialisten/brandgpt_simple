#!/usr/bin/env python3
"""
Complete end-to-end test of the RAG pipeline using the Vodafone PDF.
This tests: PDF ingestion → Vector storage → Query → Response generation
"""

import requests
import json
import time
import os
from pathlib import Path


class BrandGPTTester:
    def __init__(self, base_url="http://localhost:9700"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_credentials = {
            "username": "test_user",
            "email": "test@brandgpt.com",
            "password": "secure_password123"
        }
        self.token = None
        self.session_id = None
        self.document_id = None
    
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
            "system_prompt": "You are a helpful AI assistant specialized in analyzing business documents. "
                           "Provide detailed and accurate answers based on the document content."
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
    
    def ingest_pdf(self):
        """Ingest the Vodafone PDF document"""
        self.print_step(3, "PDF Document Ingestion")
        
        pdf_path = Path("docs/Vodafone_TestFile2.pdf")
        if not pdf_path.exists():
            print(f"❌ PDF file not found: {pdf_path}")
            return False
        
        print(f"📄 Processing PDF: {pdf_path}")
        print(f"📊 File size: {pdf_path.stat().st_size / 1024:.1f} KB")
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {"file": ("Vodafone_TestFile2.pdf", pdf_file, "application/pdf")}
            
            response = self.session.post(
                f"{self.base_url}/api/ingest/file/{self.session_id}",
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            self.document_id = result["document_id"]
            print(f"✅ PDF ingestion started")
            print(f"📄 Document ID: {self.document_id}")
            print(f"⏳ Status: {result['status']}")
            return True
        else:
            print(f"❌ PDF ingestion failed: {response.status_code} - {response.text}")
            return False
    
    def wait_for_processing(self, max_wait_seconds=60):
        """Wait for document processing to complete"""
        self.print_step(4, "Waiting for Document Processing")
        
        print("⏳ Waiting for PDF processing to complete...")
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
                        print("✅ Document processing completed successfully")
                        return True
                    elif status == "failed":
                        error = doc.get("error_message", "Unknown error")
                        print(f"❌ Document processing failed: {error}")
                        return False
                else:
                    print("⚠️  Document not found in session")
            
            time.sleep(3)
        
        print(f"⏰ Processing timeout after {max_wait_seconds} seconds")
        return False
    
    def show_document_chunks(self):
        """Display extracted document chunks"""
        self.print_step("4.5", "Extracted Document Content Preview")
        
        # Make a simple query to get some document chunks
        query_data = {
            "query": "show me document content",
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
            
            print(f"📄 Document was split into chunks. Here are some examples:")
            print(f"📊 Total chunks retrieved for preview: {len(sources)}")
            
            for i, source in enumerate(sources[:5]):  # Show first 5 chunks
                print(f"\n📄 Chunk {i+1}:")
                print(f"   Content: {source.get('text', '')[:300]}{'...' if len(source.get('text', '')) > 300 else ''}")
                if 'metadata' in source:
                    print(f"   Metadata: {source['metadata']}")
            
            if len(sources) > 5:
                print(f"\n... and {len(sources) - 5} more chunks")
        else:
            print(f"❌ Could not retrieve document chunks: {response.status_code} - {response.text}")
    
    def test_queries(self):
        """Test various queries against the ingested document"""
        self.print_step(5, "Testing Document Queries")
        
        test_queries = [
            {
                "query": "What is this document about? Please provide a detailed overview of its contents and purpose.",
                "description": "General document overview"
            },
            {
                "query": "What are the key findings, main points, or important information in this document? Please be specific and detailed.",
                "description": "Key findings extraction"
            },
            {
                "query": "List all the Vodafone products, services, or solutions mentioned in this document with their descriptions.",
                "description": "Product/service identification"
            },
            {
                "query": "Are there any specific recommendations, action items, tips, or best practices mentioned in this document?",
                "description": "Recommendations identification"
            },
            {
                "query": "What technical specifications, requirements, or configuration details are provided in this document?",
                "description": "Technical details extraction"
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
                        print(f"      Text: {source.get('text', '')}")
                        print(f"      Score: {source.get('score', 'N/A')}")
                        if 'metadata' in source:
                            print(f"      Metadata: {source['metadata']}")
                
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
        """Run the complete end-to-end test"""
        print("🚀 BrandGPT End-to-End RAG Pipeline Test")
        print("Testing with Vodafone_TestFile2.pdf")
        
        # Step 1: Authentication
        if not self.register_and_login():
            return False
        
        # Step 2: Create session
        if not self.create_session():
            return False
        
        # Step 3: Ingest PDF
        if not self.ingest_pdf():
            return False
        
        # Step 4: Wait for processing
        if not self.wait_for_processing():
            return False
        
        # Step 4.5: Show extracted document chunks
        self.show_document_chunks()
        
        # Step 5: Test queries
        results = self.test_queries()
        
        # Final summary
        self.print_step(6, "Test Results Summary")
        successful_queries = sum(1 for r in results if r["success"])
        total_queries = len(results)
        
        print(f"📊 Test Results:")
        print(f"   ✅ Successful queries: {successful_queries}/{total_queries}")
        print(f"   📄 PDF processed: docs/Vodafone_TestFile2.pdf")
        print(f"   🔗 Session ID: {self.session_id}")
        print(f"   📄 Document ID: {self.document_id}")
        
        if successful_queries == total_queries:
            print(f"\n🎉 ALL TESTS PASSED! The RAG pipeline is working correctly.")
            return True
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
            return False


if __name__ == "__main__":
    tester = BrandGPTTester()
    success = tester.run_full_test()
    exit(0 if success else 1)