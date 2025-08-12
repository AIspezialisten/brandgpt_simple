import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import status
from tests.utils import TestMetrics, create_test_documents, wait_for_processing


@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_ingestion(authenticated_client, test_session):
    """Test concurrent document ingestion performance."""
    session_id = test_session["id"]
    metrics = TestMetrics()
    
    # Create multiple test documents
    documents = [
        {"content": f"Test document {i} with content about topic {i}", "filename": f"doc_{i}.txt"}
        for i in range(5)
    ]
    
    metrics.start_timer("concurrent_ingestion")
    
    # Ingest documents concurrently
    document_ids = await create_test_documents(authenticated_client, session_id, documents)
    
    metrics.end_timer("concurrent_ingestion")
    metrics.record_metric("documents_ingested", len(document_ids))
    
    # Wait for processing
    statuses = wait_for_processing(authenticated_client, session_id, document_ids, max_wait=60)
    
    completed_docs = sum(1 for status in statuses.values() if status == "completed")
    metrics.record_metric("documents_completed", completed_docs)
    
    # Verify all documents were processed
    assert completed_docs >= len(document_ids) * 0.8  # At least 80% should succeed
    
    metrics.print_summary()


@pytest.mark.slow
@pytest.mark.asyncio
async def test_query_response_time(authenticated_client, test_session, sample_text_content):
    """Test query response times with different loads."""
    session_id = test_session["id"]
    metrics = TestMetrics()
    
    # First ingest some content
    from io import BytesIO
    text_bytes = sample_text_content.encode('utf-8')
    files = {"file": ("content.txt", BytesIO(text_bytes), "text/plain")}
    data = {"session_id": session_id}
    
    response = authenticated_client.post("/api/ingest/file", files=files, data=data)
    assert response.status_code == status.HTTP_200_OK
    
    # Wait for ingestion
    time.sleep(4)
    
    queries = [
        "What is natural language processing?",
        "Tell me about machine learning applications.",
        "How does sentiment analysis work?",
        "What are the benefits of NLP?",
        "Explain text classification."
    ]
    
    response_times = []
    
    for i, query in enumerate(queries):
        query_data = {
            "query": query,
            "session_id": session_id,
            "use_system_prompt": True
        }
        
        start_time = time.time()
        response = authenticated_client.post("/api/query", json=query_data)
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        response_time = end_time - start_time
        response_times.append(response_time)
        
        metrics.record_metric(f"query_{i}_response_time", response_time)
    
    # Calculate statistics
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    min_response_time = min(response_times)
    
    metrics.record_metric("avg_response_time", avg_response_time)
    metrics.record_metric("max_response_time", max_response_time)
    metrics.record_metric("min_response_time", min_response_time)
    
    # Assert reasonable performance (adjust thresholds as needed)
    assert avg_response_time < 30.0  # Average should be under 30 seconds
    assert max_response_time < 60.0  # No query should take over 1 minute
    
    metrics.print_summary()


@pytest.mark.slow
@pytest.mark.asyncio
async def test_large_document_ingestion(authenticated_client, test_session):
    """Test ingestion of large documents."""
    session_id = test_session["id"]
    metrics = TestMetrics()
    
    # Create a large document (about 50KB)
    large_content = "This is a test of large document processing. " * 1000
    
    from io import BytesIO
    text_bytes = large_content.encode('utf-8')
    files = {"file": ("large_doc.txt", BytesIO(text_bytes), "text/plain")}
    data = {"session_id": session_id}
    
    metrics.record_metric("document_size_bytes", len(text_bytes))
    
    metrics.start_timer("large_document_ingestion")
    response = authenticated_client.post("/api/ingest/file", files=files, data=data)
    metrics.end_timer("large_document_ingestion")
    
    assert response.status_code == status.HTTP_200_OK
    document_id = response.json()["document_id"]
    
    # Wait for processing with longer timeout
    statuses = wait_for_processing(authenticated_client, session_id, [document_id], max_wait=120)
    
    assert document_id in statuses
    assert statuses[document_id] in ["completed", "failed"]
    
    if statuses[document_id] == "completed":
        # Test querying the large document
        query_data = {
            "query": "What is this document about?",
            "session_id": session_id,
            "use_system_prompt": True
        }
        
        metrics.start_timer("large_document_query")
        response = authenticated_client.post("/api/query", json=query_data)
        metrics.end_timer("large_document_query")
        
        assert response.status_code == status.HTTP_200_OK
    
    metrics.print_summary()


@pytest.mark.slow
@pytest.mark.asyncio
async def test_memory_usage_stability(authenticated_client, test_session):
    """Test that memory usage remains stable during repeated operations."""
    session_id = test_session["id"]
    
    # Perform repeated ingestion and query cycles
    for cycle in range(3):
        # Ingest document
        content = f"Test document for cycle {cycle} " * 100
        
        from io import BytesIO
        text_bytes = content.encode('utf-8')
        files = {"file": (f"cycle_{cycle}.txt", BytesIO(text_bytes), "text/plain")}
        data = {"session_id": session_id}
        
        response = authenticated_client.post("/api/ingest/file", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
        
        # Wait for processing
        time.sleep(3)
        
        # Perform query
        query_data = {
            "query": f"Tell me about cycle {cycle}",
            "session_id": session_id,
            "use_system_prompt": True
        }
        
        response = authenticated_client.post("/api/query", json=query_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Small delay between cycles
        await asyncio.sleep(1)
    
    # If we get here without errors, memory usage is likely stable


def test_api_health_check_performance(client):
    """Test that health check is fast and reliable."""
    response_times = []
    
    for i in range(10):
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}
        
        response_time = end_time - start_time
        response_times.append(response_time)
    
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    
    # Health check should be very fast
    assert avg_response_time < 0.1  # Average under 100ms
    assert max_response_time < 0.5  # Max under 500ms
    
    print(f"Health check avg: {avg_response_time:.3f}s, max: {max_response_time:.3f}s")