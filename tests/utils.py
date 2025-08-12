"""Test utilities and helpers."""

import time
import asyncio
from typing import Dict, Any, List
from fastapi.testclient import TestClient


def wait_for_processing(
    client: TestClient,
    session_id: str,
    document_ids: List[int],
    max_wait: int = 30,
    check_interval: float = 1.0
) -> Dict[str, Any]:
    """
    Wait for document processing to complete.
    
    Args:
        client: Test client
        session_id: Session ID to check
        document_ids: List of document IDs to monitor
        max_wait: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        
    Returns:
        Dictionary with document statuses
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = client.get(f"/api/documents/{session_id}")
        
        if response.status_code != 200:
            time.sleep(check_interval)
            continue
            
        documents = response.json()
        doc_statuses = {}
        
        for doc in documents:
            if doc["id"] in document_ids:
                doc_statuses[doc["id"]] = doc["processed"]
        
        # Check if all documents are processed (completed or failed)
        if all(status in ["completed", "failed"] for status in doc_statuses.values()):
            return doc_statuses
            
        time.sleep(check_interval)
    
    # Timeout reached
    return {}


async def create_test_documents(
    client: TestClient,
    session_id: str,
    documents: List[Dict[str, str]]
) -> List[int]:
    """
    Create test documents for ingestion.
    
    Args:
        client: Test client
        session_id: Session ID
        documents: List of document dictionaries with 'content' and 'filename'
        
    Returns:
        List of document IDs
    """
    from io import BytesIO
    
    document_ids = []
    
    for doc in documents:
        content = doc["content"].encode('utf-8')
        filename = doc.get("filename", "test.txt")
        
        files = {"file": (filename, BytesIO(content), "text/plain")}
        data = {"session_id": session_id}
        
        response = client.post("/api/ingest/file", files=files, data=data)
        if response.status_code == 200:
            document_ids.append(response.json()["document_id"])
    
    return document_ids


def assert_query_contains_keywords(
    response_text: str,
    keywords: List[str],
    min_matches: int = 1
) -> bool:
    """
    Assert that a query response contains at least min_matches keywords.
    
    Args:
        response_text: The response text to check
        keywords: List of keywords to search for
        min_matches: Minimum number of keywords that must be found
        
    Returns:
        True if assertion passes
    """
    response_lower = response_text.lower()
    matches = sum(1 for keyword in keywords if keyword.lower() in response_lower)
    
    assert matches >= min_matches, (
        f"Expected at least {min_matches} keywords from {keywords} "
        f"in response, but found only {matches}. Response: {response_text[:200]}..."
    )
    
    return True


def create_sample_documents() -> List[Dict[str, str]]:
    """Create a set of sample documents for testing."""
    return [
        {
            "content": """
            Machine Learning Basics
            
            Machine learning is a method of data analysis that automates analytical model building.
            It is a branch of artificial intelligence (AI) based on the idea that systems can learn
            from data, identify patterns and make decisions with minimal human intervention.
            
            Key concepts include:
            - Supervised learning with labeled data
            - Unsupervised learning for pattern discovery
            - Deep learning with neural networks
            """,
            "filename": "ml_basics.txt"
        },
        {
            "content": """
            Natural Language Processing
            
            Natural Language Processing (NLP) is a field of AI that focuses on the interaction
            between computers and humans using natural language. The goal is to enable computers
            to understand, interpret, and generate human language in a valuable way.
            
            Applications include:
            - Sentiment analysis
            - Machine translation
            - Chatbots and virtual assistants
            - Text summarization
            """,
            "filename": "nlp_overview.txt"
        },
        {
            "content": """
            Computer Vision Fundamentals
            
            Computer vision is an interdisciplinary field that deals with how computers can be made
            to gain high-level understanding from digital images or videos. It seeks to automate
            tasks that the human visual system can do.
            
            Common tasks:
            - Image classification
            - Object detection
            - Face recognition
            - Medical image analysis
            """,
            "filename": "computer_vision.txt"
        }
    ]


class TestMetrics:
    """Helper class to collect test metrics and performance data."""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.metrics[f"{operation}_start"] = time.time()
    
    def end_timer(self, operation: str):
        """End timing an operation and record duration."""
        start_key = f"{operation}_start"
        if start_key in self.metrics:
            duration = time.time() - self.metrics[start_key]
            self.metrics[f"{operation}_duration"] = duration
            del self.metrics[start_key]
    
    def record_metric(self, name: str, value: Any):
        """Record a custom metric."""
        self.metrics[name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics."""
        return self.metrics.copy()
    
    def print_summary(self):
        """Print a summary of all metrics."""
        print("\n=== Test Metrics Summary ===")
        for name, value in self.metrics.items():
            if name.endswith("_duration"):
                print(f"{name}: {value:.2f}s")
            else:
                print(f"{name}: {value}")
        print("===========================")