"""Tests for user management endpoints."""
import pytest
from fastapi import status
import uuid


class TestGetCurrentUser:
    """Tests for GET /api/users/me endpoint."""

    def test_get_current_user_success(self, client, user_token):
        """Test getting current user info."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["role"] == "user"
        assert "id" in data

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without token."""
        response = client.get("/api/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateCurrentUser:
    """Tests for PUT /api/users/me endpoint."""

    def test_update_current_user_email(self, client, user_token):
        """Test updating user email."""
        response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_update_current_user_username(self, client, user_token):
        """Test updating username."""
        response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"username": "newusername"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "newusername"

    def test_update_current_user_password(self, client, user_token):
        """Test updating password."""
        response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"password": "newpassword123"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_current_user_multiple_fields(self, client, user_token):
        """Test updating multiple fields at once."""
        response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "email": "updated@example.com",
                "username": "updateduser"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["username"] == "updateduser"

    def test_update_current_user_unauthorized(self, client):
        """Test updating user without token."""
        response = client.put(
            "/api/users/me",
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListUsers:
    """Tests for GET /api/users endpoint."""

    def test_list_users_admin_success(self, client, admin_token, test_user):
        """Test listing users as admin."""
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(u["email"] == "test@example.com" for u in data)

    def test_list_users_with_pagination(self, client, admin_token):
        """Test listing users with skip and limit."""
        response = client.get(
            "/api/users/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_users_non_admin_forbidden(self, client, user_token):
        """Test listing users as non-admin user."""
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_unauthorized(self, client):
        """Test listing users without token."""
        response = client.get("/api/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateUser:
    """Tests for POST /api/users endpoint."""

    def test_create_user_success(self, client, admin_token):
        """Test creating a new user."""
        response = client.post(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "password_hash" not in data

    def test_create_user_duplicate_email(self, client, admin_token, test_user):
        """Test creating user with duplicate email."""
        response = client.post(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "test@example.com",
                "username": "anotheruser",
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_missing_fields(self, client, admin_token):
        """Test creating user with missing required fields."""
        response = client.post(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": "user@example.com"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_non_admin_forbidden(self, client, user_token):
        """Test creating user as non-admin."""
        response = client.post(
            "/api/users/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_unauthorized(self, client):
        """Test creating user without token."""
        response = client.post(
            "/api/users/",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUser:
    """Tests for GET /api/users/{user_id} endpoint."""

    def test_get_user_success(self, client, admin_token, test_user):
        """Test getting a specific user."""
        response = client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == "test@example.com"

    def test_get_user_not_found(self, client, admin_token):
        """Test getting non-existent user."""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_non_admin_forbidden(self, client, user_token, test_user):
        """Test getting user as non-admin."""
        response = client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_unauthorized(self, client, test_user):
        """Test getting user without token."""
        response = client.get(f"/api/users/{test_user.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateUser:
    """Tests for PUT /api/users/{user_id} endpoint."""

    def test_update_user_success(self, client, admin_token, test_user):
        """Test updating a user."""
        response = client.put(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": "updated@example.com", "username": "updated"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["username"] == "updated"

    def test_update_user_not_found(self, client, admin_token):
        """Test updating non-existent user."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user_non_admin_forbidden(self, client, user_token, test_user):
        """Test updating user as non-admin."""
        response = client.put(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_password(self, client, admin_token, test_user):
        """Test updating user password."""
        response = client.put(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"password": "newpassword123"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_user_unauthorized(self, client, test_user):
        """Test updating user without token."""
        response = client.put(
            f"/api/users/{test_user.id}",
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteUser:
    """Tests for DELETE /api/users/{user_id} endpoint."""

    def test_delete_user_success(self, client, admin_token, db_session):
        """Test deleting a user."""
        from app.models.user import User, Role
        from app.services.auth_service import hash_password

        # Create a user to delete
        user_to_delete = User(
            id=str(uuid.uuid4()),
            email="todelete@example.com",
            username="todelete",
            password_hash=hash_password("password123"),
            role=Role.USER,
            is_active=True
        )
        db_session.add(user_to_delete)
        db_session.commit()

        response = client.delete(
            f"/api/users/{user_to_delete.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify user was deleted
        deleted_user = db_session.query(User).filter(
            User.id == user_to_delete.id
        ).first()
        assert deleted_user is None

    def test_delete_user_not_found(self, client, admin_token):
        """Test deleting non-existent user."""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user_non_admin_forbidden(self, client, user_token, test_user):
        """Test deleting user as non-admin."""
        response = client.delete(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_unauthorized(self, client, test_user):
        """Test deleting user without token."""
        response = client.delete(f"/api/users/{test_user.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
