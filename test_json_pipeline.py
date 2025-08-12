#!/usr/bin/env python3
"""
Complete end-to-end test of the RAG pipeline using JSON/text ingestion.
This tests: JSON ingestion → Text extraction → Vector storage → Query → Response generation
"""

import requests
import json
import time
import os
from pathlib import Path


class BrandGPTJSONTester:
    def __init__(self, base_url="http://localhost:9700"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_credentials = {
            "username": "test_user_json",
            "email": "test_json@brandgpt.com",
            "password": "secure_password123"
        }
        self.token = None
        self.session_id = None
        self.document_id = None
        self.sample_data = self._create_sample_json()
    
    def _create_sample_json(self):
        """Create comprehensive sample JSON data for testing"""
        return {
            "company": {
                "name": "TechInnovate Solutions",
                "founded": 2020,
                "headquarters": {
                    "address": "123 Innovation Drive",
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "USA",
                    "postal_code": "94105"
                },
                "description": "A leading technology company specializing in artificial intelligence, machine learning, and data analytics solutions for enterprises.",
                "mission": "To democratize AI technology and make it accessible to businesses of all sizes.",
                "vision": "A world where every organization can harness the power of AI to solve complex problems and drive innovation."
            },
            "products": [
                {
                    "id": "ai-platform-001",
                    "name": "AI Analytics Platform",
                    "category": "Software",
                    "description": "Comprehensive AI-powered analytics platform that helps businesses extract insights from their data using machine learning algorithms.",
                    "features": [
                        "Real-time data processing",
                        "Predictive analytics",
                        "Natural language queries",
                        "Automated report generation",
                        "Custom dashboard creation"
                    ],
                    "pricing": {
                        "starter": {"price": 99, "currency": "USD", "period": "month"},
                        "professional": {"price": 299, "currency": "USD", "period": "month"},
                        "enterprise": {"price": 999, "currency": "USD", "period": "month"}
                    },
                    "target_industries": ["Finance", "Healthcare", "Retail", "Manufacturing"]
                },
                {
                    "id": "nlp-service-002", 
                    "name": "Natural Language Processing Service",
                    "category": "API Service",
                    "description": "Cloud-based NLP service offering text analysis, sentiment analysis, entity extraction, and language translation capabilities.",
                    "features": [
                        "Multilingual support (50+ languages)",
                        "Sentiment analysis with confidence scores",
                        "Named entity recognition",
                        "Text summarization",
                        "Language detection and translation"
                    ],
                    "pricing": {
                        "pay_per_use": {"price": 0.001, "currency": "USD", "unit": "request"},
                        "monthly_plan": {"price": 199, "currency": "USD", "period": "month", "included_requests": 100000}
                    },
                    "target_industries": ["Media", "Customer Service", "Content Creation", "Research"]
                }
            ],
            "employees": [
                {
                    "id": "emp-001",
                    "name": "Dr. Sarah Chen",
                    "position": "Chief Executive Officer",
                    "department": "Executive",
                    "bio": "Dr. Chen is a renowned AI researcher with over 15 years of experience in machine learning and natural language processing. She holds a PhD in Computer Science from Stanford University and has published over 50 papers in top-tier conferences.",
                    "expertise": ["Machine Learning", "Natural Language Processing", "Computer Vision", "Leadership"],
                    "education": [
                        {"degree": "PhD Computer Science", "institution": "Stanford University", "year": 2008},
                        {"degree": "MS Computer Science", "institution": "MIT", "year": 2005},
                        {"degree": "BS Mathematics", "institution": "UC Berkeley", "year": 2003}
                    ]
                },
                {
                    "id": "emp-002", 
                    "name": "Michael Rodriguez",
                    "position": "Chief Technology Officer",
                    "department": "Engineering",
                    "bio": "Michael is a seasoned technology executive with expertise in scalable systems architecture, cloud computing, and AI infrastructure. He previously led engineering teams at several successful startups.",
                    "expertise": ["System Architecture", "Cloud Computing", "DevOps", "Team Leadership"],
                    "education": [
                        {"degree": "MS Computer Engineering", "institution": "Carnegie Mellon", "year": 2010},
                        {"degree": "BS Computer Science", "institution": "University of Texas", "year": 2008}
                    ]
                }
            ],
            "financial_data": {
                "fiscal_year": 2023,
                "revenue": {
                    "total": 12500000,
                    "currency": "USD",
                    "breakdown": {
                        "product_sales": 8500000,
                        "service_revenue": 3000000,
                        "consulting": 1000000
                    }
                },
                "expenses": {
                    "total": 9800000,
                    "currency": "USD",
                    "breakdown": {
                        "personnel": 6000000,
                        "infrastructure": 1500000,
                        "marketing": 1200000,
                        "research_development": 1100000
                    }
                },
                "profit": {
                    "gross": 2700000,
                    "net": 2100000,
                    "margin_percent": 16.8
                }
            },
            "partnerships": [
                {
                    "partner": "CloudTech Inc",
                    "type": "Technology Integration",
                    "description": "Strategic partnership for cloud infrastructure and deployment solutions",
                    "start_date": "2022-03-15",
                    "status": "active"
                },
                {
                    "partner": "DataCorp Analytics",
                    "type": "Channel Partner", 
                    "description": "Reseller partnership to expand market reach in enterprise analytics",
                    "start_date": "2021-09-01",
                    "status": "active"
                }
            ],
            "awards_recognition": [
                {
                    "award": "Best AI Startup 2023",
                    "organization": "TechCrunch",
                    "date": "2023-11-15",
                    "description": "Recognized for innovative AI solutions and rapid growth"
                },
                {
                    "award": "Innovation Excellence Award",
                    "organization": "AI Innovation Council",
                    "date": "2023-06-20", 
                    "description": "Honored for breakthrough advancements in natural language processing"
                }
            ],
            "contact_information": {
                "website": "https://www.techinnovatesolutions.com",
                "email": "info@techinnovatesolutions.com",
                "phone": "+1-555-TECH-INN",
                "social_media": {
                    "linkedin": "https://linkedin.com/company/techinnovate-solutions",
                    "twitter": "https://twitter.com/TechInnovateSol",
                    "github": "https://github.com/techinnovate-solutions"
                }
            }
        }
    
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
            "system_prompt": "You are a helpful AI assistant specialized in analyzing structured business data and JSON documents. "
                           "Provide detailed and accurate answers based on the company and product information provided."
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
    
    def ingest_json_text(self):
        """Ingest JSON data as text file"""
        self.print_step(3, "JSON/Text Document Ingestion")
        
        # Convert JSON to pretty-printed text
        json_text = json.dumps(self.sample_data, indent=2, ensure_ascii=False)
        
        print(f"📄 Processing JSON data as text file")
        print(f"📊 JSON structure: Company profile with products, employees, financials")
        print(f"📈 Data size: {len(json_text)} characters, {len(json_text.split())} words")
        
        # Create a temporary file-like object for upload
        files = {
            "file": ("company_data.txt", json_text.encode('utf-8'), "text/plain")
        }
        
        response = self.session.post(
            f"{self.base_url}/api/ingest/file/{self.session_id}",
            files=files
        )
        
        if response.status_code == 200:
            result = response.json()
            self.document_id = result["document_id"]
            print(f"✅ JSON/Text ingestion started")
            print(f"📄 Document ID: {self.document_id}")
            print(f"⏳ Status: {result['status']}")
            return True
        else:
            print(f"❌ JSON/Text ingestion failed: {response.status_code} - {response.text}")
            return False
    
    def wait_for_processing(self, max_wait_seconds=60):
        """Wait for document processing to complete"""
        self.print_step(4, "Waiting for Document Processing")
        
        print("⏳ Waiting for JSON/text processing to complete...")
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
    
    def show_processed_content(self):
        """Display processed content chunks"""
        self.print_step("4.5", "Processed JSON Content Preview")
        
        # Make a simple query to get some content chunks
        query_data = {
            "query": "show me information about the company",
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
            
            print(f"📄 JSON data was processed and chunked. Here are some examples:")
            print(f"📊 Total chunks retrieved for preview: {len(sources)}")
            
            for i, source in enumerate(sources[:5]):  # Show first 5 chunks
                print(f"\n📄 Chunk {i+1}:")
                content = source.get('text', '')
                print(f"   Content: {content[:400]}{'...' if len(content) > 400 else ''}")
                if 'metadata' in source:
                    metadata = source['metadata']
                    print(f"   Source: {metadata.get('filename', 'N/A')}")
                    print(f"   Document ID: {metadata.get('document_id', 'N/A')}")
            
            if len(sources) > 5:
                print(f"\n... and {len(sources) - 5} more chunks")
        else:
            print(f"❌ Could not retrieve processed content: {response.status_code} - {response.text}")
    
    def test_queries(self):
        """Test various queries against the JSON data"""
        self.print_step(5, "Testing Queries on JSON Data")
        
        test_queries = [
            {
                "query": "What is TechInnovate Solutions and what do they do? Provide a comprehensive overview.",
                "description": "Company overview"
            },
            {
                "query": "What products does TechInnovate Solutions offer? List all products with their descriptions and features.",
                "description": "Product catalog"
            },
            {
                "query": "Who are the key executives at TechInnovate Solutions? What are their backgrounds and expertise?",
                "description": "Executive team"
            },
            {
                "query": "What are TechInnovate Solutions' financial results for 2023? Include revenue, expenses, and profit details.",
                "description": "Financial performance"
            },
            {
                "query": "What pricing does TechInnovate Solutions offer for their AI Analytics Platform?",
                "description": "Pricing information"
            },
            {
                "query": "What partnerships and awards has TechInnovate Solutions received?",
                "description": "Partnerships and recognition"
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
                    for j, source in enumerate(sources[:3]):  # Show first 3 sources
                        print(f"\n   📄 Source {j+1}:")
                        content = source.get('text', '')
                        print(f"      Text: {content[:200]}{'...' if len(content) > 200 else ''}")
                        print(f"      Score: {source.get('score', 'N/A')}")
                        if 'metadata' in source:
                            metadata = source['metadata']
                            print(f"      Filename: {metadata.get('filename', 'N/A')}")
                
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
        """Run the complete end-to-end JSON ingestion test"""
        print("🚀 BrandGPT End-to-End JSON/Text Ingestion Pipeline Test")
        print("Testing with comprehensive company data JSON")
        
        # Step 1: Authentication
        if not self.register_and_login():
            return False
        
        # Step 2: Create session
        if not self.create_session():
            return False
        
        # Step 3: Ingest JSON as text
        if not self.ingest_json_text():
            return False
        
        # Step 4: Wait for processing
        if not self.wait_for_processing():
            return False
        
        # Step 4.5: Show processed content
        self.show_processed_content()
        
        # Step 5: Test queries
        results = self.test_queries()
        
        # Final summary
        self.print_step(6, "Test Results Summary")
        successful_queries = sum(1 for r in results if r["success"])
        total_queries = len(results)
        
        print(f"📊 Test Results:")
        print(f"   ✅ Successful queries: {successful_queries}/{total_queries}")
        print(f"   📄 JSON data processed: Company profile with {len(self.sample_data)} main sections")
        print(f"   🔗 Session ID: {self.session_id}")
        print(f"   📄 Document ID: {self.document_id}")
        
        if successful_queries == total_queries:
            print(f"\n🎉 ALL TESTS PASSED! The JSON/text ingestion pipeline is working correctly.")
            return True
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
            return False


if __name__ == "__main__":
    tester = BrandGPTJSONTester()
    success = tester.run_full_test()
    exit(0 if success else 1)