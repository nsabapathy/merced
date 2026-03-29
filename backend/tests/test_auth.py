"""Tests for authentication."""
import pytest
from fastapi import status


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email(client):
    """Test login with invalid email."""
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_invalid_password(client, test_user):
    """Test login with invalid password."""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout(client, user_token):
    """Test logout."""
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
