"""Tests for model configuration endpoints."""
import pytest
from fastapi import status
import uuid


class TestListModels:
    """Tests for GET /api/models endpoint."""

    def test_list_models_admin_sees_all(self, client, admin_token, db_session):
        """Test admin sees all active models."""
        # Create a model
        client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Test Model",
                "base_url": "https://api.example.com",
                "api_key": "test-key-123",
                "model_id": "gpt-4",
                "is_active": True
            }
        )

        response = client.get(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert any(m["name"] == "Test Model" for m in data)

    def test_list_models_user_no_permissions(self, client, user_token):
        """Test regular user with no permissions sees no models."""
        response = client.get(
            "/api/models/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # User has no group permissions, should see no models
        assert len(data) == 0

    def test_list_models_user_with_all_models_permission(
        self, client, user_token, admin_token, db_session, test_user
    ):
        """Test user with NULL model_id permission sees all models."""
        from app.models.group import Group, GroupMembership, GroupPermission

        # Create model
        model_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Public Model",
                "base_url": "https://api.example.com",
                "api_key": "test-key",
                "model_id": "gpt-4",
                "is_active": True
            }
        )
        model_id = model_response.json()["id"]

        # Create group
        group = Group(
            id=str(uuid.uuid4()),
            name="All Users",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        # Add user to group
        membership = GroupMembership(
            id=str(uuid.uuid4()),
            group_id=group.id,
            user_id=test_user.id
        )
        db_session.add(membership)
        db_session.commit()

        # Grant permission to all models (model_id=NULL)
        permission = GroupPermission(
            id=str(uuid.uuid4()),
            group_id=group.id,
            model_id=None,  # NULL = all models
            collection_id=None
        )
        db_session.add(permission)
        db_session.commit()

        response = client.get(
            "/api/models/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(m["id"] == model_id for m in data)

    def test_list_models_excludes_inactive(self, client, admin_token):
        """Test list excludes inactive models."""
        # Create inactive model
        client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Inactive Model",
                "base_url": "https://api.example.com",
                "api_key": "test-key",
                "model_id": "old-model",
                "is_active": False
            }
        )

        response = client.get(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert not any(m["name"] == "Inactive Model" for m in data)

    def test_list_models_unauthorized(self, client):
        """Test listing without token."""
        response = client.get("/api/models/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateModel:
    """Tests for POST /api/models endpoint."""

    def test_create_model_admin_success(self, client, admin_token):
        """Test admin can create a model."""
        response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "GPT-4 Turbo",
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-test-123",
                "model_id": "gpt-4-turbo",
                "is_active": True
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "GPT-4 Turbo"
        assert data["base_url"] == "https://api.openai.com/v1"
        assert data["model_id"] == "gpt-4-turbo"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        # API key should not be returned
        assert "api_key" not in data

    def test_create_model_default_active(self, client, admin_token):
        """Test model defaults to active."""
        response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Default Model",
                "base_url": "https://api.example.com",
                "api_key": "test-key",
                "model_id": "default-model"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_active"] is True

    def test_create_model_duplicate_name(self, client, admin_token):
        """Test creating model with duplicate name fails."""
        # Create first model
        client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Unique Name",
                "base_url": "https://api.example.com",
                "api_key": "key1",
                "model_id": "model1"
            }
        )

        # Try to create with same name
        response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Unique Name",
                "base_url": "https://other.com",
                "api_key": "key2",
                "model_id": "model2"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_model_missing_required_fields(self, client, admin_token):
        """Test creating model with missing fields."""
        response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Incomplete"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_model_non_admin_forbidden(self, client, user_token):
        """Test non-admin cannot create model."""
        response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Unauthorized Model",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "model"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_model_unauthorized(self, client):
        """Test creating model without token."""
        response = client.post(
            "/api/models/",
            json={
                "name": "Unauthorized",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "model"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetModel:
    """Tests for GET /api/models/{model_id} endpoint."""

    def test_get_model_admin_success(self, client, admin_token):
        """Test admin can get any model."""
        # Create model
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Admin Model",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "admin-model"
            }
        )
        model_id = create_response.json()["id"]

        response = client.get(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == model_id
        assert data["name"] == "Admin Model"

    def test_get_model_user_with_permission(
        self, client, user_token, admin_token, db_session, test_user
    ):
        """Test user with permission can get model."""
        from app.models.group import Group, GroupMembership, GroupPermission

        # Create model
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Accessible Model",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "accessible"
            }
        )
        model_id = create_response.json()["id"]

        # Create group with permission
        group = Group(
            id=str(uuid.uuid4()),
            name="Model Users",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        membership = GroupMembership(
            id=str(uuid.uuid4()),
            group_id=group.id,
            user_id=test_user.id
        )
        db_session.add(membership)
        db_session.commit()

        permission = GroupPermission(
            id=str(uuid.uuid4()),
            group_id=group.id,
            model_id=model_id,
            collection_id=None
        )
        db_session.add(permission)
        db_session.commit()

        response = client.get(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == model_id

    def test_get_model_user_no_permission(self, client, user_token, admin_token):
        """Test user without permission cannot get model."""
        # Create model
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Restricted Model",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "restricted"
            }
        )
        model_id = create_response.json()["id"]

        response = client.get(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_nonexistent_model(self, client, admin_token):
        """Test getting non-existent model."""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/models/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_model_unauthorized(self, client):
        """Test getting model without token."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/models/{fake_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateModel:
    """Tests for PUT /api/models/{model_id} endpoint."""

    def test_update_model_admin_success(self, client, admin_token):
        """Test admin can update model."""
        # Create model
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Original",
                "base_url": "https://api.example.com",
                "api_key": "key1",
                "model_id": "original"
            }
        )
        model_id = create_response.json()["id"]

        # Update model
        response = client.put(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Updated",
                "base_url": "https://new.api.com",
                "api_key": "key2",
                "model_id": "updated",
                "is_active": False
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated"
        assert data["base_url"] == "https://new.api.com"
        assert data["model_id"] == "updated"
        assert data["is_active"] is False

    def test_update_model_partial(self, client, admin_token):
        """Test updating only some fields."""
        # Create model
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Original Name",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "original"
            }
        )
        model_id = create_response.json()["id"]

        # Update only name
        response = client.put(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "New Name"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["base_url"] == "https://api.example.com"
        assert data["model_id"] == "original"

    def test_update_model_activate_deactivate(self, client, admin_token):
        """Test activating/deactivating model."""
        # Create inactive model
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Togglable",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "togglable",
                "is_active": False
            }
        )
        model_id = create_response.json()["id"]

        # Activate it
        response = client.put(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": True}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_active"] is True

    def test_update_model_not_found(self, client, admin_token):
        """Test updating non-existent model."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/models/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_model_non_admin_forbidden(self, client, user_token, admin_token):
        """Test non-admin cannot update model."""
        # Create model as admin
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Admin Model",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "admin"
            }
        )
        model_id = create_response.json()["id"]

        # Try to update as regular user
        response = client.put(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"name": "Hacked"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_model_unauthorized(self, client, admin_token):
        """Test updating model without token."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/models/{fake_id}",
            json={"name": "Updated"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteModel:
    """Tests for DELETE /api/models/{model_id} endpoint."""

    def test_delete_model_admin_success(self, client, admin_token):
        """Test admin can delete model."""
        # Create model
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "To Delete",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "deleteme"
            }
        )
        model_id = create_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify it's gone
        get_response = client.get(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_model_not_found(self, client, admin_token):
        """Test deleting non-existent model."""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/models/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_model_non_admin_forbidden(self, client, user_token, admin_token):
        """Test non-admin cannot delete model."""
        # Create model as admin
        create_response = client.post(
            "/api/models/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Protected",
                "base_url": "https://api.example.com",
                "api_key": "key",
                "model_id": "protected"
            }
        )
        model_id = create_response.json()["id"]

        # Try to delete as regular user
        response = client.delete(
            f"/api/models/{model_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_model_unauthorized(self, client):
        """Test deleting model without token."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/models/{fake_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
