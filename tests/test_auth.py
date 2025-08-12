import pytest
from fastapi import status


def test_user_registration(client, test_user_credentials):
    """Test user registration endpoint."""
    response = client.post("/api/auth/register", json=test_user_credentials)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["username"] == test_user_credentials["username"]
    assert data["email"] == test_user_credentials["email"]
    assert "hashed_password" not in data
    assert data["is_active"] is True


def test_duplicate_user_registration(client, test_user_credentials):
    """Test that duplicate user registration fails."""
    # Register user first time
    response = client.post("/api/auth/register", json=test_user_credentials)
    assert response.status_code == status.HTTP_200_OK
    
    # Try to register same user again
    response = client.post("/api/auth/register", json=test_user_credentials)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_user_login(client, test_user_credentials):
    """Test user login and token generation."""
    # Register user first
    response = client.post("/api/auth/register", json=test_user_credentials)
    assert response.status_code == status.HTTP_200_OK
    
    # Login
    login_data = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"]
    }
    response = client.post(
        "/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_login(client, test_user_credentials):
    """Test login with invalid credentials."""
    # Register user first
    response = client.post("/api/auth/register", json=test_user_credentials)
    assert response.status_code == status.HTTP_200_OK
    
    # Try to login with wrong password
    login_data = {
        "username": test_user_credentials["username"],
        "password": "wrongpassword"
    }
    response = client.post(
        "/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_without_auth(client):
    """Test that protected endpoints require authentication."""
    response = client.get("/api/sessions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_with_auth(authenticated_client):
    """Test that authenticated users can access protected endpoints."""
    response = authenticated_client.get("/api/sessions")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)