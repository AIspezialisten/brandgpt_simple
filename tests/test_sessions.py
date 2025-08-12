import pytest
from fastapi import status


def test_create_session(authenticated_client):
    """Test creating a new session."""
    session_data = {
        "system_prompt": "You are a helpful AI assistant specialized in technology."
    }
    response = authenticated_client.post("/api/sessions", json=session_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "id" in data
    assert data["system_prompt"] == session_data["system_prompt"]
    assert data["user_id"] is not None


def test_create_session_with_prompt_id(authenticated_client):
    """Test creating a session with a predefined prompt."""
    # First create a prompt
    prompt_data = {
        "name": "Tech Assistant",
        "description": "A prompt for technology questions",
        "content": "You are an expert in technology and software development."
    }
    response = authenticated_client.post("/api/prompts", json=prompt_data)
    assert response.status_code == status.HTTP_200_OK
    prompt_id = response.json()["id"]
    
    # Create session with the prompt
    session_data = {"prompt_id": prompt_id}
    response = authenticated_client.post("/api/sessions", json=session_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["prompt_id"] == prompt_id


def test_list_sessions(authenticated_client):
    """Test listing user sessions."""
    # Create a few sessions
    for i in range(3):
        session_data = {"system_prompt": f"Assistant {i}"}
        response = authenticated_client.post("/api/sessions", json=session_data)
        assert response.status_code == status.HTTP_200_OK
    
    # List sessions
    response = authenticated_client.get("/api/sessions")
    assert response.status_code == status.HTTP_200_OK
    
    sessions = response.json()
    assert len(sessions) == 3


def test_create_prompt(authenticated_client):
    """Test creating a system prompt."""
    prompt_data = {
        "name": "Science Tutor",
        "description": "A helpful science tutor",
        "content": "You are a knowledgeable science tutor who explains concepts clearly."
    }
    response = authenticated_client.post("/api/prompts", json=prompt_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["name"] == prompt_data["name"]
    assert data["description"] == prompt_data["description"]
    assert data["content"] == prompt_data["content"]
    assert "id" in data


def test_list_prompts(authenticated_client):
    """Test listing prompts."""
    # Create a few prompts
    prompts = [
        {"name": "Math Tutor", "content": "You help with math problems."},
        {"name": "History Expert", "content": "You are a history expert."},
    ]
    
    for prompt_data in prompts:
        response = authenticated_client.post("/api/prompts", json=prompt_data)
        assert response.status_code == status.HTTP_200_OK
    
    # List prompts
    response = authenticated_client.get("/api/prompts")
    assert response.status_code == status.HTTP_200_OK
    
    retrieved_prompts = response.json()
    assert len(retrieved_prompts) >= 2  # At least the ones we created