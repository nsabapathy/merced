"""
Wiring tests for the get_current_user dependency.

These tests use `real_client` — a test client that does NOT override
get_current_user — so they exercise the actual FastAPI dependency injection
chain. A broken dependency (e.g. always returning None for the token) will
cause these tests to fail with 401/422 even if all other tests pass.
"""
import pytest
from fastapi import status


class TestGetCurrentUserWiring:
    """Verify that get_current_user correctly extracts the Bearer token."""

    def test_authenticated_request_succeeds(self, real_client, test_user, user_token):
        """A valid Bearer token must reach the handler and return 200."""
        response = real_client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK, (
            "get_current_user failed to extract the Bearer token from the "
            "Authorization header. Check that the dependency uses HTTPBearer(), "
            f"not a stub. Response: {response.json()}"
        )
        assert response.json()["email"] == test_user.email

    def test_missing_token_returns_401(self, real_client):
        """A request with no Authorization header must return 401/403."""
        response = real_client.get("/api/users/me")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_invalid_token_returns_401(self, real_client):
        """A request with a bogus token must return 401."""
        response = real_client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer not_a_real_jwt"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_then_use_token_end_to_end(self, real_client, test_user):
        """Full login → use token flow without any dependency overrides."""
        # Step 1: log in with real credentials
        login_resp = real_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "password123"}
        )
        assert login_resp.status_code == status.HTTP_200_OK
        token = login_resp.json()["access_token"]

        # Step 2: use the returned token on a protected endpoint
        me_resp = real_client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == status.HTTP_200_OK, (
            "Login succeeded but the returned token was rejected by "
            "/api/users/me. This means get_current_user is not reading "
            f"the Authorization header correctly. Response: {me_resp.json()}"
        )
        assert me_resp.json()["email"] == test_user.email
