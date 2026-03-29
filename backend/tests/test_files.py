"""Tests for file upload/download endpoints."""
import io
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status

from app.models.file import File


FAKE_BLOB_PATH = "/tmp/uploads/user-id/test-file.txt"


@pytest.fixture
def mock_storage():
    """Mock storage service for all file tests."""
    with patch("app.routers.files.storage_service") as mock:
        mock.upload_file = AsyncMock(return_value=(FAKE_BLOB_PATH, FAKE_BLOB_PATH))
        mock.get_download_url = AsyncMock(return_value="http://storage/test-file.txt")
        mock.delete_file = AsyncMock(return_value=None)
        yield mock


def _make_upload_response(client, user_token, filename="test.txt", content=b"hello"):
    return client.post(
        "/api/files/upload",
        files={"file": (filename, io.BytesIO(content), "text/plain")},
        headers={"Authorization": f"Bearer {user_token}"},
    )


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def test_upload_file(client, user_token, db_session, test_user, mock_storage):
    """Successful upload creates a DB record and returns FileRead."""
    response = _make_upload_response(client, user_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["original_name"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert data["size_bytes"] == 5  # len(b"hello")
    assert data["user_id"] == test_user.id
    assert "id" in data

    # Verify record persisted in DB
    record = db_session.query(File).filter(File.id == data["id"]).first()
    assert record is not None
    assert record.original_name == "test.txt"


def test_upload_empty_file(client, user_token, mock_storage):
    """Uploading an empty file returns 400."""
    mock_storage.upload_file = AsyncMock(side_effect=ValueError("Empty file"))
    response = _make_upload_response(client, user_token, content=b"")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_upload_requires_auth(client, mock_storage):
    """Upload without token returns 401."""
    response = client.post(
        "/api/files/upload",
        files={"file": ("test.txt", io.BytesIO(b"data"), "text/plain")},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_upload_storage_error_returns_400(client, user_token, mock_storage):
    """Storage failure propagates as 400."""
    mock_storage.upload_file = AsyncMock(side_effect=RuntimeError("Azure down"))
    response = _make_upload_response(client, user_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Get file info
# ---------------------------------------------------------------------------

def test_get_file(client, user_token, db_session, test_user, mock_storage):
    """Owner can retrieve file metadata."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.get(
        f"/api/files/{file_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == file_id


def test_get_file_not_found(client, user_token):
    """Requesting a non-existent file returns 404."""
    response = client.get(
        f"/api/files/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_file_other_user_returns_404(
    client, user_token, admin_token, db_session, test_user, test_admin, mock_storage
):
    """Another user cannot see a file they don't own (returns 404, not 403)."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.get(
        f"/api/files/{file_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_file_requires_auth(client, mock_storage, user_token, db_session, test_user):
    """Unauthenticated request returns 401."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.get(f"/api/files/{file_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Download URL
# ---------------------------------------------------------------------------

def test_get_download_url(client, user_token, db_session, test_user, mock_storage):
    """Owner receives a download URL."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.get(
        f"/api/files/{file_id}/download",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "download_url" in response.json()


def test_get_download_url_not_found(client, user_token):
    """Non-existent file returns 404."""
    response = client.get(
        f"/api/files/{uuid.uuid4()}/download",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_download_url_storage_error(client, user_token, db_session, test_user, mock_storage):
    """Storage error when generating URL returns 400."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    mock_storage.get_download_url = AsyncMock(side_effect=RuntimeError("Storage error"))
    response = client.get(
        f"/api/files/{file_id}/download",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_download_url_other_user_returns_404(
    client, user_token, admin_token, db_session, test_user, test_admin, mock_storage
):
    """Another user cannot download a file they don't own."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.get(
        f"/api/files/{file_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_file(client, user_token, db_session, test_user, mock_storage):
    """Owner can delete a file; record is removed from DB."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.delete(
        f"/api/files/{file_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "File deleted"

    # Confirm removal from DB
    assert db_session.query(File).filter(File.id == file_id).first() is None


def test_delete_file_not_found(client, user_token):
    """Deleting a non-existent file returns 404."""
    response = client.delete(
        f"/api/files/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_file_other_user_returns_404(
    client, user_token, admin_token, db_session, test_user, test_admin, mock_storage
):
    """Another user cannot delete a file they don't own."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.delete(
        f"/api/files/{file_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Original file still in DB
    assert db_session.query(File).filter(File.id == file_id).first() is not None


def test_delete_file_storage_error_still_removes_record(
    client, user_token, db_session, test_user, mock_storage
):
    """Storage deletion failure is tolerated; DB record is still removed."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    mock_storage.delete_file = AsyncMock(side_effect=RuntimeError("Storage unavailable"))
    response = client.delete(
        f"/api/files/{file_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert db_session.query(File).filter(File.id == file_id).first() is None


def test_delete_requires_auth(client, mock_storage, user_token, db_session, test_user):
    """Unauthenticated delete returns 401."""
    upload = _make_upload_response(client, user_token)
    file_id = upload.json()["id"]

    response = client.delete(f"/api/files/{file_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
