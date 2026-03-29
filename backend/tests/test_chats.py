"""Tests for chat functionality."""
import pytest
from fastapi import status


def test_create_chat(client, user_token, db_session, test_user):
    """Test creating a chat."""
    response = client.post(
        "/api/chats/",
        json={"title": "Test Chat"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Chat"
    assert data["user_id"] == test_user.id


def test_list_chats(client, user_token, db_session, test_user):
    """Test listing chats."""
    # Create a chat first
    client.post(
        "/api/chats/",
        json={"title": "Test Chat"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    response = client.get(
        "/api/chats/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_chat_detail(client, user_token, db_session, test_user):
    """Test getting chat detail."""
    # Create a chat first
    create_response = client.post(
        "/api/chats/",
        json={"title": "Test Chat"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    chat_id = create_response.json()["id"]

    response = client.get(
        f"/api/chats/{chat_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == chat_id
    assert data["title"] == "Test Chat"


def test_update_chat(client, user_token, db_session, test_user):
    """Test updating a chat."""
    # Create a chat first
    create_response = client.post(
        "/api/chats/",
        json={"title": "Test Chat"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    chat_id = create_response.json()["id"]

    response = client.put(
        f"/api/chats/{chat_id}",
        json={"title": "Updated Chat"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Chat"


def test_delete_chat(client, user_token, db_session, test_user):
    """Test deleting a chat."""
    # Create a chat first
    create_response = client.post(
        "/api/chats/",
        json={"title": "Test Chat"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    chat_id = create_response.json()["id"]

    response = client.delete(
        f"/api/chats/{chat_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
