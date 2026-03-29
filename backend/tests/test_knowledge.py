"""Tests for knowledge/RAG functionality."""
import pytest
from fastapi import status


def test_create_collection(client, user_token, db_session, test_user):
    """Test creating a knowledge collection."""
    response = client.post(
        "/api/knowledge/",
        json={"name": "Test Collection"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Collection"
    assert data["created_by"] == test_user.id


def test_list_collections(client, user_token, db_session, test_user):
    """Test listing knowledge collections."""
    # Create a collection first
    client.post(
        "/api/knowledge/",
        json={"name": "Test Collection"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    response = client.get(
        "/api/knowledge/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_get_collection(client, user_token, db_session, test_user):
    """Test getting a collection."""
    # Create a collection first
    create_response = client.post(
        "/api/knowledge/",
        json={"name": "Test Collection"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    collection_id = create_response.json()["id"]

    response = client.get(
        f"/api/knowledge/{collection_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == collection_id


def test_delete_collection(client, user_token, db_session, test_user):
    """Test deleting a collection."""
    # Create a collection first
    create_response = client.post(
        "/api/knowledge/",
        json={"name": "Test Collection"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    collection_id = create_response.json()["id"]

    response = client.delete(
        f"/api/knowledge/{collection_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
