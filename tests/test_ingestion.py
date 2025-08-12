import pytest
import json
import time
from fastapi import status
from io import BytesIO


def test_ingest_pdf_file(authenticated_client, test_session, sample_pdf_path):
    """Test PDF file ingestion."""
    session_id = test_session["id"]
    
    with open(sample_pdf_path, 'rb') as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        
        response = authenticated_client.post(
            f"/api/ingest/file/{session_id}",
            files=files
        )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "document_id" in result
    assert result["status"] == "processing"
    
    # Wait a bit for background processing
    time.sleep(2)
    
    # Check document status
    response = authenticated_client.get(f"/api/documents/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    
    documents = response.json()
    assert len(documents) >= 1
    doc = next((d for d in documents if d["id"] == result["document_id"]), None)
    assert doc is not None
    assert doc["content_type"] == "pdf"


def test_ingest_text_file(authenticated_client, test_session, sample_text_content):
    """Test text file ingestion."""
    session_id = test_session["id"]
    
    text_bytes = sample_text_content.encode('utf-8')
    files = {"file": ("test.txt", BytesIO(text_bytes), "text/plain")}
    
    response = authenticated_client.post(
        f"/api/ingest/file/{session_id}",
        files=files
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "document_id" in result
    assert result["status"] == "processing"
    
    # Wait for processing
    time.sleep(2)
    
    # Check document status
    response = authenticated_client.get(f"/api/documents/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    
    documents = response.json()
    doc = next((d for d in documents if d["id"] == result["document_id"]), None)
    assert doc is not None
    assert doc["content_type"] == "text"


def test_ingest_json_file(authenticated_client, test_session, sample_json_content):
    """Test JSON file ingestion."""
    session_id = test_session["id"]
    
    json_bytes = json.dumps(sample_json_content).encode('utf-8')
    files = {"file": ("test.json", BytesIO(json_bytes), "application/json")}
    
    response = authenticated_client.post(
        f"/api/ingest/file/{session_id}",
        files=files
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "document_id" in result
    assert result["status"] == "processing"
    
    # Wait for processing
    time.sleep(2)
    
    # Check document status
    response = authenticated_client.get(f"/api/documents/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    
    documents = response.json()
    doc = next((d for d in documents if d["id"] == result["document_id"]), None)
    assert doc is not None
    assert doc["content_type"] == "text"  # JSON gets processed as text currently


@pytest.mark.asyncio
async def test_ingest_url(authenticated_client, test_session, mock_url_server):
    """Test URL ingestion."""
    session_id = test_session["id"]
    
    url_data = {
        "session_id": session_id,
        "content_type": "url",
        "url": f"{mock_url_server}/index.html",
        "max_depth": 2
    }
    
    response = authenticated_client.post("/api/ingest/url", json=url_data)
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "document_id" in result
    assert result["status"] == "processing"
    
    # Wait longer for URL processing (includes scraping)
    time.sleep(5)
    
    # Check document status
    response = authenticated_client.get(f"/api/documents/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    
    documents = response.json()
    doc = next((d for d in documents if d["id"] == result["document_id"]), None)
    assert doc is not None
    assert doc["content_type"] == "url"


def test_ingest_with_invalid_session(authenticated_client):
    """Test that ingestion fails with invalid session ID."""
    text_bytes = b"Test content"
    files = {"file": ("test.txt", BytesIO(text_bytes), "text/plain")}
    
    response = authenticated_client.post(
        "/api/ingest/file/invalid-session-id",
        files=files
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session not found" in response.json()["detail"]


def test_list_documents(authenticated_client, test_session, sample_text_content):
    """Test listing documents for a session."""
    session_id = test_session["id"]
    
    # Ingest a few documents
    text_bytes = sample_text_content.encode('utf-8')
    for i in range(2):
        files = {"file": (f"test{i}.txt", BytesIO(text_bytes), "text/plain")}
        
        response = authenticated_client.post(
            f"/api/ingest/file/{session_id}",
            files=files
        )
        assert response.status_code == status.HTTP_200_OK
    
    # List documents
    response = authenticated_client.get(f"/api/documents/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    
    documents = response.json()
    assert len(documents) >= 2  # At least the ones we just created


def test_list_documents_invalid_session(authenticated_client):
    """Test that listing documents fails for invalid session."""
    response = authenticated_client.get("/api/documents/invalid-session-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND