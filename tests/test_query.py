import pytest
import time
from fastapi import status
from io import BytesIO


@pytest.mark.asyncio
async def test_query_without_documents(authenticated_client, test_session):
    """Test querying without any ingested documents."""
    query_data = {
        "query": "What is machine learning?",
        "session_id": test_session["id"],
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)
    # Should have no sources since no documents are ingested
    assert len(result["sources"]) == 0


@pytest.mark.asyncio
async def test_query_with_documents(authenticated_client, test_session, sample_text_content):
    """Test querying after ingesting documents."""
    session_id = test_session["id"]
    
    # First, ingest some content
    text_bytes = sample_text_content.encode('utf-8')
    files = {"file": ("nlp_info.txt", BytesIO(text_bytes), "text/plain")}
    data = {"session_id": session_id}
    
    response = authenticated_client.post(
        "/api/ingest/file",
        files=files,
        data=data
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Wait for ingestion to complete
    time.sleep(3)
    
    # Now query for information
    query_data = {
        "query": "What are the key applications of NLP?",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)
    
    # Should have relevant information about NLP applications
    response_text = result["response"].lower()
    assert any(keyword in response_text for keyword in [
        "text classification", "sentiment analysis", "machine translation", 
        "question answering", "nlp", "natural language"
    ])


@pytest.mark.asyncio
async def test_query_with_pdf_content(authenticated_client, test_session, sample_pdf_path):
    """Test querying after ingesting PDF content."""
    session_id = test_session["id"]
    
    # Ingest PDF
    with open(sample_pdf_path, 'rb') as f:
        files = {"file": ("ai_doc.pdf", f, "application/pdf")}
        data = {"session_id": session_id}
        
        response = authenticated_client.post(
            "/api/ingest/file",
            files=files,
            data=data
        )
    
    assert response.status_code == status.HTTP_200_OK
    
    # Wait for processing
    time.sleep(4)
    
    # Query about the PDF content
    query_data = {
        "query": "What is machine learning?",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result
    assert "sources" in result
    
    # Should contain information from the PDF
    response_text = result["response"].lower()
    assert any(keyword in response_text for keyword in [
        "machine learning", "artificial intelligence", "ai", "data"
    ])


@pytest.mark.asyncio
async def test_query_without_session_id(authenticated_client):
    """Test global query without specific session."""
    query_data = {
        "query": "Tell me about quantum computing",
        "use_system_prompt": False
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result
    assert "sources" in result
    # Should work but might have no sources if no global documents


@pytest.mark.asyncio
async def test_query_with_system_prompt(authenticated_client, test_session):
    """Test that system prompts are used in queries."""
    session_id = test_session["id"]
    
    # The test session has a system prompt: "You are a helpful assistant"
    query_data = {
        "query": "Hello, who are you?",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    response_text = result["response"].lower()
    # Should reflect the system prompt in some way
    assert any(keyword in response_text for keyword in [
        "assistant", "helpful", "help"
    ])


@pytest.mark.asyncio
async def test_query_without_system_prompt(authenticated_client, test_session):
    """Test querying without using system prompt."""
    query_data = {
        "query": "What is 2 + 2?",
        "session_id": test_session["id"],
        "use_system_prompt": False
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result


def test_query_requires_authentication(client):
    """Test that query endpoint requires authentication."""
    query_data = {
        "query": "Test query",
    }
    
    response = client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_query_invalid_session(authenticated_client):
    """Test querying with invalid session ID."""
    query_data = {
        "query": "Test query",
        "session_id": "invalid-session-id",
        "use_system_prompt": True
    }
    
    # This should still work - just won't find session-specific documents
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_query_multiple_documents(authenticated_client, test_session, sample_text_content):
    """Test querying with multiple documents to verify retrieval and reranking."""
    session_id = test_session["id"]
    
    # Ingest multiple related documents
    documents = [
        "Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
        "Natural language processing helps computers understand human language.",
        "Computer vision enables machines to interpret visual information from images.",
        "Reinforcement learning teaches AI systems through rewards and penalties."
    ]
    
    for i, content in enumerate(documents):
        text_bytes = content.encode('utf-8')
        files = {"file": (f"doc_{i}.txt", BytesIO(text_bytes), "text/plain")}
        data = {"session_id": session_id}
        
        response = authenticated_client.post(
            "/api/ingest/file",
            files=files,
            data=data
        )
        assert response.status_code == status.HTTP_200_OK
    
    # Wait for processing
    time.sleep(5)
    
    # Query for specific information
    query_data = {
        "query": "How does deep learning work with neural networks?",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result
    assert "sources" in result
    assert len(result["sources"]) > 0
    
    # Should contain information about deep learning and neural networks
    response_text = result["response"].lower()
    assert any(keyword in response_text for keyword in [
        "deep learning", "neural network", "layers"
    ])