"""Tests for prompt management endpoints."""
import pytest
from fastapi import status
import uuid


class TestListPrompts:
    """Tests for GET /api/prompts endpoint."""

    def test_list_prompts_own_only(self, client, user_token, db_session, test_user):
        """Test listing user's own private prompts."""
        # Create a private prompt
        client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Private Prompt",
                "content": "This is private",
                "is_public": False
            }
        )

        response = client.get(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(p["title"] == "Private Prompt" for p in data)

    def test_list_prompts_includes_public(self, client, user_token, admin_token, db_session):
        """Test listing includes public prompts from other users."""
        # Create public prompt as admin
        client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Public Prompt",
                "content": "This is public",
                "is_public": True
            }
        )

        # User should see the public prompt
        response = client.get(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(p["title"] == "Public Prompt" and p["is_public"] for p in data)

    def test_list_prompts_excludes_private_others(self, client, user_token, admin_token):
        """Test listing excludes private prompts from other users."""
        # Create private prompt as admin
        client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Admin Private",
                "content": "Admin only",
                "is_public": False
            }
        )

        # User should not see the private prompt
        response = client.get(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert not any(p["title"] == "Admin Private" for p in data)

    def test_list_prompts_with_pagination(self, client, user_token):
        """Test listing with skip and limit."""
        response = client.get(
            "/api/prompts/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_prompts_unauthorized(self, client):
        """Test listing without token."""
        response = client.get("/api/prompts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreatePrompt:
    """Tests for POST /api/prompts endpoint."""

    def test_create_prompt_success(self, client, user_token, test_user):
        """Test creating a prompt."""
        response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Test Prompt",
                "content": "This is test content",
                "is_public": False
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Test Prompt"
        assert data["content"] == "This is test content"
        assert data["is_public"] is False
        assert data["user_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_prompt_public(self, client, user_token, test_user):
        """Test creating a public prompt."""
        response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Public Prompt",
                "content": "Publicly shared",
                "is_public": True
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_public"] is True

    def test_create_prompt_default_private(self, client, user_token):
        """Test that prompts default to private."""
        response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Default",
                "content": "No is_public specified"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_public"] is False

    def test_create_prompt_missing_title(self, client, user_token):
        """Test creating prompt without title."""
        response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"content": "Missing title"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_prompt_missing_content(self, client, user_token):
        """Test creating prompt without content."""
        response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"title": "Missing content"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_prompt_unauthorized(self, client):
        """Test creating prompt without token."""
        response = client.post(
            "/api/prompts/",
            json={
                "title": "Unauthorized",
                "content": "No token"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetPrompt:
    """Tests for GET /api/prompts/{prompt_id} endpoint."""

    def test_get_own_private_prompt(self, client, user_token):
        """Test getting own private prompt."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Own Prompt",
                "content": "Private content",
                "is_public": False
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.get(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == prompt_id
        assert data["title"] == "Own Prompt"

    def test_get_public_prompt_other_user(self, client, user_token, admin_token):
        """Test getting public prompt from other user."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Shared Prompt",
                "content": "Publicly available",
                "is_public": True
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.get(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == prompt_id

    def test_get_private_prompt_forbidden(self, client, user_token, admin_token):
        """Test getting private prompt from other user returns 403."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Admin Private",
                "content": "Not shared",
                "is_public": False
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.get(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_nonexistent_prompt(self, client, user_token):
        """Test getting non-existent prompt."""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/prompts/{fake_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_prompt_unauthorized(self, client):
        """Test getting prompt without token."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/prompts/{fake_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdatePrompt:
    """Tests for PUT /api/prompts/{prompt_id} endpoint."""

    def test_update_prompt_title(self, client, user_token):
        """Test updating prompt title."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Original Title",
                "content": "Content"
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.put(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"title": "Updated Title"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Content"

    def test_update_prompt_content(self, client, user_token):
        """Test updating prompt content."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Title",
                "content": "Original Content"
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.put(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"content": "Updated Content"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Title"
        assert data["content"] == "Updated Content"

    def test_update_prompt_visibility(self, client, user_token):
        """Test updating prompt visibility."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Private",
                "content": "Content",
                "is_public": False
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.put(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"is_public": True}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_public"] is True

    def test_update_prompt_all_fields(self, client, user_token):
        """Test updating all fields at once."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Old",
                "content": "Old content",
                "is_public": False
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.put(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "New",
                "content": "New content",
                "is_public": True
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New"
        assert data["content"] == "New content"
        assert data["is_public"] is True

    def test_update_prompt_not_found(self, client, user_token):
        """Test updating non-existent prompt."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/prompts/{fake_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"title": "Updated"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_others_prompt_forbidden(self, client, user_token, admin_token):
        """Test updating other user's prompt."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Admin Prompt",
                "content": "Admin content"
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.put(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"title": "Hacked"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_prompt_unauthorized(self, client):
        """Test updating prompt without token."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/prompts/{fake_id}",
            json={"title": "Updated"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeletePrompt:
    """Tests for DELETE /api/prompts/{prompt_id} endpoint."""

    def test_delete_prompt_success(self, client, user_token):
        """Test deleting own prompt."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "To Delete",
                "content": "Temporary"
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.delete(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify it's deleted
        get_response = client.get(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_others_prompt_forbidden(self, client, user_token, admin_token):
        """Test deleting other user's prompt."""
        create_response = client.post(
            "/api/prompts/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Admin Prompt",
                "content": "Admin content"
            }
        )
        prompt_id = create_response.json()["id"]

        response = client.delete(
            f"/api/prompts/{prompt_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_prompt(self, client, user_token):
        """Test deleting non-existent prompt."""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/prompts/{fake_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_prompt_unauthorized(self, client):
        """Test deleting prompt without token."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/prompts/{fake_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
