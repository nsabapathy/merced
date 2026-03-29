"""Tests for group management endpoints."""
import pytest
from fastapi import status
import uuid


class TestListGroups:
    """Tests for GET /api/groups endpoint."""

    def test_list_groups_admin_success(self, client, admin_token):
        """Test listing groups as admin."""
        response = client.get(
            "/api/groups/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_groups_with_pagination(self, client, admin_token):
        """Test listing groups with skip and limit."""
        response = client.get(
            "/api/groups/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_groups_non_admin_forbidden(self, client, user_token):
        """Test listing groups as non-admin user."""
        response = client.get(
            "/api/groups/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_groups_unauthorized(self, client):
        """Test listing groups without token."""
        response = client.get("/api/groups/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateGroup:
    """Tests for POST /api/groups endpoint."""

    def test_create_group_success(self, client, admin_token):
        """Test creating a new group."""
        response = client.post(
            "/api/groups/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Engineering",
                "description": "Engineering team"
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        data = response.json()
        assert data["name"] == "Engineering"
        assert data["description"] == "Engineering team"
        assert "id" in data

    def test_create_group_minimal(self, client, admin_token):
        """Test creating group with only name."""
        response = client.post(
            "/api/groups/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Sales"}
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        data = response.json()
        assert data["name"] == "Sales"

    def test_create_group_missing_name(self, client, admin_token):
        """Test creating group without name."""
        response = client.post(
            "/api/groups/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"description": "Missing name"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_group_non_admin_forbidden(self, client, user_token):
        """Test creating group as non-admin."""
        response = client.post(
            "/api/groups/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"name": "Unauthorized Group"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_group_unauthorized(self, client):
        """Test creating group without token."""
        response = client.post(
            "/api/groups/",
            json={"name": "Unauthorized Group"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetGroup:
    """Tests for GET /api/groups/{group_id} endpoint."""

    def test_get_group_success(self, client, admin_token, db_session):
        """Test getting a specific group."""
        from app.models.group import Group

        # Create test group
        group = Group(
            id=str(uuid.uuid4()),
            name="Test Group",
            description="Test description",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.get(
            f"/api/groups/{group.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == group.id
        assert data["name"] == "Test Group"

    def test_get_group_not_found(self, client, admin_token):
        """Test getting non-existent group."""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/groups/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_group_non_admin_forbidden(self, client, user_token, db_session):
        """Test getting group as non-admin."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Admin Group",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.get(
            f"/api/groups/{group.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_group_unauthorized(self, client, db_session):
        """Test getting group without token."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Unauth Group",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.get(f"/api/groups/{group.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateGroup:
    """Tests for PUT /api/groups/{group_id} endpoint."""

    def test_update_group_success(self, client, admin_token, db_session):
        """Test updating a group."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Original Name",
            description="Original description",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Name", "description": "Updated description"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    def test_update_group_partial(self, client, admin_token, db_session):
        """Test updating only group name."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Original",
            description="Keep this",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "New Name"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Keep this"

    def test_update_group_not_found(self, client, admin_token):
        """Test updating non-existent group."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/groups/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_group_non_admin_forbidden(self, client, user_token, db_session):
        """Test updating group as non-admin."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"name": "Updated"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_group_unauthorized(self, client, db_session):
        """Test updating group without token."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}",
            json={"name": "Updated"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteGroup:
    """Tests for DELETE /api/groups/{group_id} endpoint."""

    def test_delete_group_success(self, client, admin_token, db_session):
        """Test deleting a group."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="To Delete",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()
        group_id = group.id

        response = client.delete(
            f"/api/groups/{group_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify group was deleted
        deleted_group = db_session.query(Group).filter(Group.id == group_id).first()
        assert deleted_group is None

    def test_delete_group_not_found(self, client, admin_token):
        """Test deleting non-existent group."""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/groups/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_group_non_admin_forbidden(self, client, user_token, db_session):
        """Test deleting group as non-admin."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Protected",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.delete(
            f"/api/groups/{group.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_group_unauthorized(self, client, db_session):
        """Test deleting group without token."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Unauth",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.delete(f"/api/groups/{group.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAddGroupMember:
    """Tests for POST /api/groups/{group_id}/members endpoint."""

    def test_add_member_success(self, client, admin_token, test_user, db_session):
        """Test adding a member to a group."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test Group",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.post(
            f"/api/groups/{group.id}/members",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": test_user.id}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_add_member_invalid_group(self, client, admin_token, test_user):
        """Test adding member to non-existent group."""
        fake_id = str(uuid.uuid4())
        response = client.post(
            f"/api/groups/{fake_id}/members",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": test_user.id}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_member_non_admin_forbidden(self, client, user_token, test_user, db_session):
        """Test adding member as non-admin."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.post(
            f"/api/groups/{group.id}/members",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"user_id": test_user.id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_member_unauthorized(self, client, test_user, db_session):
        """Test adding member without token."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.post(
            f"/api/groups/{group.id}/members",
            json={"user_id": test_user.id}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRemoveGroupMember:
    """Tests for DELETE /api/groups/{group_id}/members/{user_id} endpoint."""

    def test_remove_member_success(self, client, admin_token, test_user, db_session):
        """Test removing a member from a group."""
        from app.models.group import Group, GroupMembership

        group = Group(
            id=str(uuid.uuid4()),
            name="Test Group",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        # Add member first
        membership = GroupMembership(
            id=str(uuid.uuid4()),
            group_id=group.id,
            user_id=test_user.id
        )
        db_session.add(membership)
        db_session.commit()

        response = client.delete(
            f"/api/groups/{group.id}/members/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify membership was deleted
        deleted_membership = db_session.query(GroupMembership).filter(
            GroupMembership.group_id == group.id,
            GroupMembership.user_id == test_user.id
        ).first()
        assert deleted_membership is None

    def test_remove_member_not_found(self, client, admin_token, test_user, db_session):
        """Test removing member who is not in group."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.delete(
            f"/api/groups/{group.id}/members/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_member_non_admin_forbidden(self, client, user_token, test_user, db_session):
        """Test removing member as non-admin."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.delete(
            f"/api/groups/{group.id}/members/{test_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_remove_member_unauthorized(self, client, test_user, db_session):
        """Test removing member without token."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.delete(
            f"/api/groups/{group.id}/members/{test_user.id}"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateGroupPermissions:
    """Tests for PUT /api/groups/{group_id}/permissions endpoint."""

    def test_update_permissions_success(self, client, admin_token, db_session):
        """Test updating group permissions."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test Group",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "permissions": [
                    {"model_id": "model-1", "collection_id": "collection-1"},
                    {"model_id": None, "collection_id": None}
                ]
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_permissions_empty(self, client, admin_token, db_session):
        """Test clearing permissions."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"permissions": []}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_permissions_invalid_group(self, client, admin_token):
        """Test updating permissions for non-existent group."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/groups/{fake_id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"permissions": []}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_permissions_non_admin_forbidden(self, client, user_token, db_session):
        """Test updating permissions as non-admin."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}/permissions",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"permissions": []}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_permissions_unauthorized(self, client, db_session):
        """Test updating permissions without token."""
        from app.models.group import Group

        group = Group(
            id=str(uuid.uuid4()),
            name="Test",
            created_by=None
        )
        db_session.add(group)
        db_session.commit()

        response = client.put(
            f"/api/groups/{group.id}/permissions",
            json={"permissions": []}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
