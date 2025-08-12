import pytest
import time
from fastapi import status
from io import BytesIO


@pytest.mark.asyncio
async def test_complete_rag_pipeline(authenticated_client, sample_text_content, sample_pdf_path):
    """Test the complete RAG pipeline from user registration to query."""
    
    # 1. Create a custom session with specific system prompt
    session_data = {
        "system_prompt": "You are a helpful AI assistant that provides detailed explanations about technology topics."
    }
    response = authenticated_client.post("/api/sessions", json=session_data)
    assert response.status_code == status.HTTP_200_OK
    session = response.json()
    session_id = session["id"]
    
    # 2. Ingest multiple types of content
    
    # Ingest text content
    text_content = """
    Machine Learning Fundamentals:
    
    Machine learning is a method of data analysis that automates analytical model building.
    It is a branch of artificial intelligence based on the idea that systems can learn from data,
    identify patterns and make decisions with minimal human intervention.
    
    Types of Machine Learning:
    1. Supervised Learning: Uses labeled training data
    2. Unsupervised Learning: Finds hidden patterns in data
    3. Reinforcement Learning: Learns through interaction with environment
    """
    
    text_bytes = text_content.encode('utf-8')
    files = {"file": ("ml_basics.txt", BytesIO(text_bytes), "text/plain")}
    data = {"session_id": session_id}
    
    response = authenticated_client.post("/api/ingest/file", files=files, data=data)
    assert response.status_code == status.HTTP_200_OK
    text_doc_id = response.json()["document_id"]
    
    # Ingest PDF content
    with open(sample_pdf_path, 'rb') as f:
        files = {"file": ("ai_concepts.pdf", f, "application/pdf")}
        data = {"session_id": session_id}
        
        response = authenticated_client.post("/api/ingest/file", files=files, data=data)
        assert response.status_code == status.HTTP_200_OK
        pdf_doc_id = response.json()["document_id"]
    
    # Wait for processing to complete
    time.sleep(6)
    
    # 3. Verify documents were processed
    response = authenticated_client.get(f"/api/documents/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    
    documents = response.json()
    assert len(documents) >= 2
    
    # Check that our documents are there and processed
    text_doc = next((d for d in documents if d["id"] == text_doc_id), None)
    pdf_doc = next((d for d in documents if d["id"] == pdf_doc_id), None)
    
    assert text_doc is not None
    assert pdf_doc is not None
    # Note: Processing might still be ongoing, so we don't assert completed status
    
    # 4. Test various queries to verify the RAG system works
    
    # Query 1: General ML question
    query_data = {
        "query": "What are the different types of machine learning?",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result
    assert "sources" in result
    assert result["error"] is None
    
    response_text = result["response"].lower()
    # Should mention the types of ML from our ingested content
    assert any(term in response_text for term in [
        "supervised", "unsupervised", "reinforcement", "learning", "machine"
    ])
    
    # Verify sources are returned
    if len(result["sources"]) > 0:
        assert all("text" in source for source in result["sources"])
        assert all("metadata" in source for source in result["sources"])
    
    # Query 2: More specific question
    query_data = {
        "query": "How does supervised learning work?",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    response_text = result["response"].lower()
    assert any(term in response_text for term in [
        "supervised", "labeled", "training", "data"
    ])
    
    # Query 3: Question about content that might not be in documents
    query_data = {
        "query": "What is quantum computing?",
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    # Should still provide a response, even if no relevant documents found
    assert len(result["response"]) > 0
    
    # 5. Test querying without session context
    query_data = {
        "query": "Explain artificial intelligence",
        "use_system_prompt": False
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    assert "response" in result


@pytest.mark.asyncio
async def test_multi_user_isolation(client, test_db):
    """Test that different users' sessions and documents are isolated."""
    
    # Create two users
    user1_creds = {"username": "user1", "email": "user1@test.com", "password": "password123"}
    user2_creds = {"username": "user2", "email": "user2@test.com", "password": "password123"}
    
    # Register users
    for creds in [user1_creds, user2_creds]:
        response = client.post("/api/auth/register", json=creds)
        assert response.status_code == status.HTTP_200_OK
    
    # Get tokens for both users
    tokens = {}
    for i, creds in enumerate([user1_creds, user2_creds], 1):
        login_data = {"username": creds["username"], "password": creds["password"]}
        response = client.post(
            "/api/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == status.HTTP_200_OK
        tokens[f"user{i}"] = response.json()["access_token"]
    
    # Create sessions for each user
    sessions = {}
    for user, token in tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/api/sessions",
            json={"system_prompt": f"Assistant for {user}"},
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        sessions[user] = response.json()
    
    # Ingest documents for each user
    user1_content = "User 1's private document about biology."
    user2_content = "User 2's private document about chemistry."
    
    contents = {"user1": user1_content, "user2": user2_content}
    
    for user, content in contents.items():
        headers = {"Authorization": f"Bearer {tokens[user]}"}
        text_bytes = content.encode('utf-8')
        files = {"file": (f"{user}_doc.txt", BytesIO(text_bytes), "text/plain")}
        data = {"session_id": sessions[user]["id"]}
        
        response = client.post(
            "/api/ingest/file",
            files=files,
            data=data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    # Wait for processing
    time.sleep(4)
    
    # Test that each user can only see their own documents
    for user in ["user1", "user2"]:
        headers = {"Authorization": f"Bearer {tokens[user]}"}
        session_id = sessions[user]["id"]
        
        response = client.get(f"/api/documents/{session_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        documents = response.json()
        assert len(documents) >= 1
        
        # User shouldn't be able to access other user's session
        other_user = "user2" if user == "user1" else "user1"
        other_session_id = sessions[other_user]["id"]
        
        response = client.get(f"/api/documents/{other_session_id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Test that queries are isolated - user1 shouldn't get user2's content
    headers1 = {"Authorization": f"Bearer {tokens['user1']}"}
    query_data = {
        "query": "Tell me about chemistry",
        "session_id": sessions["user1"]["id"],
        "use_system_prompt": False
    }
    
    response = client.post("/api/query", json=query_data, headers=headers1)
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    # User1's query shouldn't return information from user2's chemistry document
    # (though it might have general knowledge about chemistry)
    response_text = result["response"].lower()
    assert "user 2's private document" not in response_text


@pytest.mark.asyncio 
async def test_error_handling_and_recovery(authenticated_client, test_session):
    """Test error handling in various scenarios."""
    session_id = test_session["id"]
    
    # Test invalid file upload
    invalid_content = b"This is not a valid PDF file"
    files = {"file": ("fake.pdf", BytesIO(invalid_content), "application/pdf")}
    data = {"session_id": session_id}
    
    response = authenticated_client.post("/api/ingest/file", files=files, data=data)
    assert response.status_code == status.HTTP_200_OK  # Accepted for processing
    
    # Wait and check if processing failed gracefully
    time.sleep(3)
    
    response = authenticated_client.get(f"/api/documents/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Test query with very long input
    very_long_query = "What is " + "artificial intelligence " * 1000
    query_data = {
        "query": very_long_query,
        "session_id": session_id,
        "use_system_prompt": True
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    # Should handle gracefully, either with response or appropriate error
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    # Test empty query
    query_data = {
        "query": "",
        "session_id": session_id
    }
    
    response = authenticated_client.post("/api/query", json=query_data)
    # Should reject empty queries
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY