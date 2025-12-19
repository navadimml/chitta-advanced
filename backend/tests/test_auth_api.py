"""
Integration tests for Auth API endpoints.

Tests HTTP endpoints with TestClient and in-memory database.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.base import Base
from app.db import get_uow
from app.db.repositories import UnitOfWork
from app.main import app


# =============================================================================
# Test Fixtures for API Tests
# =============================================================================

@pytest.fixture
def api_engine():
    """Create synchronous test engine for TestClient."""
    # TestClient runs synchronously, so we need a sync-compatible approach
    # We'll override the dependency
    return None


@pytest.fixture
def api_client():
    """Create API test client with dependency overrides."""
    # We need to set up the database for each test
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    # Create fresh in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async def setup_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(setup_db())

    # Create session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Override dependency
    async def override_get_uow():
        async with async_session_maker() as session:
            # Pass session to constructor - repositories are initialized lazily via properties
            uow = UnitOfWork(session=session)
            try:
                yield uow
                await uow.commit()
            except Exception:
                await uow.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_uow] = override_get_uow

    with TestClient(app) as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.fixture
def registered_user(api_client):
    """Register a user and return credentials."""
    response = api_client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "display_name": "Test User",
        }
    )
    assert response.status_code == 201, f"Registration failed: {response.text}"

    return {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "display_name": "Test User",
        "user_id": response.json()["id"],
    }


@pytest.fixture
def auth_tokens(api_client, registered_user):
    """Login and return tokens."""
    response = api_client.post(
        "/api/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        }
    )
    assert response.status_code == 200, f"Login failed: {response.text}"

    data = response.json()
    return {
        **registered_user,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


# =============================================================================
# Registration Tests
# =============================================================================

class TestRegisterEndpoint:
    """Test POST /api/auth/register."""

    def test_register_success(self, api_client):
        """Successful registration returns 201 with user data."""
        response = api_client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "display_name": "New User",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["display_name"] == "New User"
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_email(self, api_client, registered_user):
        """Registration with existing email returns 400."""
        response = api_client.post(
            "/api/auth/register",
            json={
                "email": registered_user["email"],
                "password": "AnotherPassword123!",
                "display_name": "Another User",
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, api_client):
        """Registration with invalid email returns 422."""
        response = api_client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePassword123!",
                "display_name": "New User",
            }
        )

        assert response.status_code == 422

    def test_register_short_password(self, api_client):
        """Registration with short password returns 422."""
        response = api_client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",
                "display_name": "New User",
            }
        )

        assert response.status_code == 422

    def test_register_missing_fields(self, api_client):
        """Registration with missing fields returns 422."""
        response = api_client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                # Missing password and display_name
            }
        )

        assert response.status_code == 422


# =============================================================================
# Login Tests
# =============================================================================

class TestLoginEndpoint:
    """Test POST /api/auth/login."""

    def test_login_success(self, api_client, registered_user):
        """Successful login returns 200 with tokens."""
        response = api_client.post(
            "/api/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_at" in data

    def test_login_wrong_password(self, api_client, registered_user):
        """Login with wrong password returns 401."""
        response = api_client.post(
            "/api/auth/login",
            json={
                "email": registered_user["email"],
                "password": "WrongPassword123!",
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, api_client):
        """Login with nonexistent email returns 401."""
        response = api_client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!",
            }
        )

        assert response.status_code == 401

    def test_login_invalid_email_format(self, api_client):
        """Login with invalid email format returns 422."""
        response = api_client.post(
            "/api/auth/login",
            json={
                "email": "not-an-email",
                "password": "SomePassword123!",
            }
        )

        assert response.status_code == 422


# =============================================================================
# Token Refresh Tests
# =============================================================================

class TestRefreshEndpoint:
    """Test POST /api/auth/refresh."""

    def test_refresh_success(self, api_client, auth_tokens):
        """Successful refresh returns new tokens."""
        response = api_client.post(
            "/api/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be different
        assert data["refresh_token"] != auth_tokens["refresh_token"]

    def test_refresh_invalid_token(self, api_client):
        """Refresh with invalid token returns 401."""
        response = api_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401

    def test_refresh_token_reuse_detected(self, api_client, auth_tokens):
        """Using old refresh token after refresh fails."""
        old_token = auth_tokens["refresh_token"]

        # First refresh
        response1 = api_client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_token}
        )
        assert response1.status_code == 200

        # Try to use old token again (should fail - token reuse)
        response2 = api_client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_token}
        )
        assert response2.status_code == 401


# =============================================================================
# Logout Tests
# =============================================================================

class TestLogoutEndpoint:
    """Test POST /api/auth/logout."""

    def test_logout_success(self, api_client, auth_tokens):
        """Successful logout returns success message."""
        response = api_client.post(
            "/api/auth/logout",
            json={"refresh_token": auth_tokens["refresh_token"]}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_logout_invalidates_refresh_token(self, api_client, auth_tokens):
        """After logout, refresh token no longer works."""
        # Logout
        api_client.post(
            "/api/auth/logout",
            json={"refresh_token": auth_tokens["refresh_token"]}
        )

        # Try to refresh
        response = api_client.post(
            "/api/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]}
        )

        assert response.status_code == 401


# =============================================================================
# Current User Tests
# =============================================================================

class TestMeEndpoint:
    """Test GET /api/auth/me."""

    def test_me_success(self, api_client, auth_tokens):
        """Authenticated request returns user info."""
        response = api_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == auth_tokens["email"]
        assert data["display_name"] == auth_tokens["display_name"]

    def test_me_no_token(self, api_client):
        """Request without token returns 401."""
        response = api_client.get("/api/auth/me")

        assert response.status_code == 401

    def test_me_invalid_token(self, api_client):
        """Request with invalid token returns 401."""
        response = api_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401


# =============================================================================
# Password Change Tests
# =============================================================================

class TestChangePasswordEndpoint:
    """Test POST /api/auth/change-password."""

    def test_change_password_success(self, api_client, auth_tokens):
        """Successful password change returns 200."""
        response = api_client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={
                "current_password": auth_tokens["password"],
                "new_password": "NewSecurePassword456!",
            }
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Old password should no longer work
        login_response = api_client.post(
            "/api/auth/login",
            json={
                "email": auth_tokens["email"],
                "password": auth_tokens["password"],
            }
        )
        assert login_response.status_code == 401

        # New password should work
        login_response = api_client.post(
            "/api/auth/login",
            json={
                "email": auth_tokens["email"],
                "password": "NewSecurePassword456!",
            }
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, api_client, auth_tokens):
        """Change password with wrong current password returns 400."""
        response = api_client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewSecurePassword456!",
            }
        )

        assert response.status_code == 400

    def test_change_password_no_auth(self, api_client):
        """Change password without auth returns 401."""
        response = api_client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Whatever123!",
                "new_password": "NewSecurePassword456!",
            }
        )

        assert response.status_code == 401


# =============================================================================
# Password Reset Tests
# =============================================================================

class TestForgotPasswordEndpoint:
    """Test POST /api/auth/forgot-password."""

    def test_forgot_password_existing_user(self, api_client, registered_user):
        """Forgot password for existing user returns success."""
        response = api_client.post(
            "/api/auth/forgot-password",
            json={"email": registered_user["email"]}
        )

        assert response.status_code == 200
        # Should not reveal whether user exists
        assert "if an account" in response.json()["message"].lower()

    def test_forgot_password_nonexistent_user(self, api_client):
        """Forgot password for nonexistent user returns success (no reveal)."""
        response = api_client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200
        # Same message for security


class TestResetPasswordEndpoint:
    """Test POST /api/auth/reset-password."""

    def test_reset_password_invalid_token(self, api_client):
        """Reset password with invalid token returns 400."""
        response = api_client.post(
            "/api/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "NewSecurePassword456!",
            }
        )

        assert response.status_code == 400


# =============================================================================
# Email Verification Tests
# =============================================================================

class TestVerifyEmailEndpoint:
    """Test POST /api/auth/verify-email."""

    def test_verify_email_invalid_token(self, api_client):
        """Verify email with invalid token returns 400."""
        response = api_client.post(
            "/api/auth/verify-email",
            json={"token": "invalid-token"}
        )

        assert response.status_code == 400


class TestResendVerificationEndpoint:
    """Test POST /api/auth/resend-verification."""

    def test_resend_verification_success(self, api_client, registered_user):
        """Resend verification returns success."""
        response = api_client.post(
            "/api/auth/resend-verification",
            json={"email": registered_user["email"]}
        )

        assert response.status_code == 200

    def test_resend_verification_nonexistent(self, api_client):
        """Resend for nonexistent email returns success (no reveal)."""
        response = api_client.post(
            "/api/auth/resend-verification",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200


# =============================================================================
# Logout All Devices Tests
# =============================================================================

class TestLogoutAllEndpoint:
    """Test POST /api/auth/logout-all."""

    def test_logout_all_success(self, api_client, auth_tokens):
        """Logout all devices returns success."""
        response = api_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"}
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    def test_logout_all_invalidates_refresh_token(self, api_client, auth_tokens):
        """After logout-all, refresh token no longer works."""
        # Logout all
        api_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"}
        )

        # Try to refresh
        response = api_client.post(
            "/api/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]}
        )

        assert response.status_code == 401

    def test_logout_all_no_auth(self, api_client):
        """Logout-all without auth returns 401."""
        response = api_client.post("/api/auth/logout-all")

        assert response.status_code == 401
