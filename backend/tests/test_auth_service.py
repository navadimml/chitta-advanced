"""
Integration tests for Auth Service.

Tests authentication operations with database (in-memory SQLite).
Uses async fixtures from conftest.py.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta

from app.services.auth.service import (
    AuthService,
    AuthResult,
    RegistrationResult,
)
from app.services.auth.password import hash_password


class TestUserRegistration:
    """Test user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, uow):
        """Successful registration returns user and no errors."""
        result = await auth_service.register(
            email="new@example.com",
            password="SecurePassword123!",
            display_name="New User",
            require_email_verification=False,
        )

        assert result.success is True
        assert result.user is not None
        assert result.user.email == "new@example.com"
        assert result.user.display_name == "New User"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_register_with_verification(self, auth_service, uow):
        """Registration with email verification returns token."""
        result = await auth_service.register(
            email="verify@example.com",
            password="SecurePassword123!",
            display_name="Verify User",
            require_email_verification=True,
        )

        assert result.success is True
        assert result.verification_token is not None
        assert result.user.email_verified is False

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, test_user, uow):
        """Registration with existing email fails."""
        result = await auth_service.register(
            email=test_user["email"],
            password="DifferentPassword123!",
            display_name="Different User",
            require_email_verification=False,
        )

        assert result.success is False
        assert result.error == "Email already registered"
        assert result.user is None

    @pytest.mark.asyncio
    async def test_register_password_is_hashed(self, auth_service, uow):
        """Password is stored as hash, not plaintext."""
        password = "PlainTextPassword123!"
        result = await auth_service.register(
            email="hash@example.com",
            password=password,
            display_name="Hash User",
            require_email_verification=False,
        )

        assert result.user.password_hash is not None
        assert result.user.password_hash != password
        assert result.user.password_hash.startswith("$2b$")  # bcrypt


class TestUserLogin:
    """Test user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, test_user, uow):
        """Successful login returns user and tokens."""
        result = await auth_service.login(
            email=test_user["email"],
            password=test_user["password"],
        )

        assert result.success is True
        assert result.user is not None
        assert result.user.email == test_user["email"]
        assert result.tokens is not None
        assert result.tokens.access_token is not None
        assert result.tokens.refresh_token is not None

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, test_user, uow):
        """Login with wrong password fails."""
        result = await auth_service.login(
            email=test_user["email"],
            password="WrongPassword123!",
        )

        assert result.success is False
        assert result.error == "Invalid email or password"
        assert result.tokens is None

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, auth_service, uow):
        """Login with nonexistent email fails."""
        result = await auth_service.login(
            email="nonexistent@example.com",
            password="SomePassword123!",
        )

        assert result.success is False
        assert result.error == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_login_unverified_email_requires_verification(
        self, auth_service, uow
    ):
        """Login with unverified email and require_verified=True fails."""
        # Register with verification required
        reg_result = await auth_service.register(
            email="unverified@example.com",
            password="Password123!",
            display_name="Unverified User",
            require_email_verification=True,
        )
        await uow.commit()

        # Try to login requiring verified email
        result = await auth_service.login(
            email="unverified@example.com",
            password="Password123!",
            require_verified_email=True,
        )

        assert result.success is False
        assert result.requires_verification is True
        assert "verify your email" in result.error.lower()

    @pytest.mark.asyncio
    async def test_login_unverified_email_allowed(self, auth_service, uow):
        """Login with unverified email succeeds when not required."""
        # Register with verification required
        await auth_service.register(
            email="unverified2@example.com",
            password="Password123!",
            display_name="Unverified User",
            require_email_verification=True,
        )
        await uow.commit()

        # Login without requiring verified email
        result = await auth_service.login(
            email="unverified2@example.com",
            password="Password123!",
            require_verified_email=False,
        )

        assert result.success is True
        assert result.tokens is not None

    @pytest.mark.asyncio
    async def test_login_records_login_time(self, auth_service, test_user, uow):
        """Successful login updates last_login_at."""
        before = datetime.now(timezone.utc)

        result = await auth_service.login(
            email=test_user["email"],
            password=test_user["password"],
        )
        await uow.commit()

        after = datetime.now(timezone.utc)

        # Refresh user from db
        user = await uow.users.get_by_id(result.user.id)

        assert user.last_login_at is not None
        # Note: SQLite returns naive datetime
        if user.last_login_at.tzinfo is None:
            assert before.replace(tzinfo=None) <= user.last_login_at <= after.replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_login_clears_failed_attempts(self, auth_service, test_user, uow):
        """Successful login resets failed_login_attempts."""
        # First fail some logins
        for _ in range(3):
            await auth_service.login(
                email=test_user["email"],
                password="WrongPassword!",
            )
        await uow.commit()

        # Check failed attempts increased
        user = await uow.users.get_by_email(test_user["email"])
        assert user.failed_login_attempts == 3

        # Now succeed
        result = await auth_service.login(
            email=test_user["email"],
            password=test_user["password"],
        )
        await uow.commit()

        # Check failed attempts reset
        user = await uow.users.get_by_id(result.user.id)
        assert user.failed_login_attempts == 0


class TestTokenRefresh:
    """Test token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_tokens_success(self, auth_service, authenticated_user, uow):
        """Token refresh returns new tokens."""
        result = await auth_service.refresh_tokens(
            authenticated_user["refresh_token"]
        )

        assert result.success is True
        assert result.tokens is not None
        assert result.tokens.access_token is not None
        assert result.tokens.refresh_token is not None
        # New tokens should be different
        assert result.tokens.refresh_token != authenticated_user["refresh_token"]

    @pytest.mark.asyncio
    async def test_refresh_tokens_old_token_revoked(
        self, auth_service, authenticated_user, uow
    ):
        """After refresh, old token is revoked."""
        old_refresh = authenticated_user["refresh_token"]

        # First refresh succeeds
        result1 = await auth_service.refresh_tokens(old_refresh)
        await uow.commit()
        assert result1.success is True

        # Using old token again fails (token reuse detection)
        result2 = await auth_service.refresh_tokens(old_refresh)

        assert result2.success is False
        # Family should be revoked due to reuse
        assert "security" in result2.error.lower() or "invalid" in result2.error.lower()

    @pytest.mark.asyncio
    async def test_refresh_tokens_expired(self, auth_service, uow):
        """Expired refresh token fails."""
        # Create user and get tokens
        reg = await auth_service.register(
            email="expired@example.com",
            password="Password123!",
            display_name="Expired User",
            require_email_verification=False,
        )
        await uow.commit()

        login = await auth_service.login(
            email="expired@example.com",
            password="Password123!",
        )
        await uow.commit()

        # Manually expire the token in DB
        token_hash = auth_service.token_service.get_token_hash(
            login.tokens.refresh_token
        )
        stored = await uow.refresh_tokens.get_by_token_hash(token_hash)
        stored.expires_at = datetime.utcnow() - timedelta(hours=1)
        await uow.commit()

        # Try to refresh
        result = await auth_service.refresh_tokens(login.tokens.refresh_token)

        assert result.success is False
        assert "expired" in result.error.lower()

    @pytest.mark.asyncio
    async def test_refresh_tokens_invalid(self, auth_service, uow):
        """Invalid refresh token fails."""
        result = await auth_service.refresh_tokens("not.a.valid.token")

        assert result.success is False


class TestLogout:
    """Test logout functionality."""

    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, authenticated_user, uow):
        """Logout revokes refresh token."""
        result = await auth_service.logout(authenticated_user["refresh_token"])
        await uow.commit()

        assert result is True

        # Token should no longer work for refresh
        refresh_result = await auth_service.refresh_tokens(
            authenticated_user["refresh_token"]
        )
        assert refresh_result.success is False

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, auth_service, uow):
        """Logout with invalid token returns False."""
        result = await auth_service.logout("invalid.token.here")

        assert result is False

    @pytest.mark.asyncio
    async def test_logout_all_devices(self, auth_service, uow):
        """logout_all_devices revokes all user's tokens."""
        # Create user
        reg = await auth_service.register(
            email="multi@example.com",
            password="Password123!",
            display_name="Multi Device User",
            require_email_verification=False,
        )
        await uow.commit()

        # Login multiple times (simulate multiple devices)
        tokens_list = []
        for _ in range(3):
            login = await auth_service.login(
                email="multi@example.com",
                password="Password123!",
            )
            await uow.commit()
            tokens_list.append(login.tokens.refresh_token)

        # Logout all devices
        count = await auth_service.logout_all_devices(reg.user.id)
        await uow.commit()

        assert count == 3

        # All tokens should be invalid
        for token in tokens_list:
            result = await auth_service.refresh_tokens(token)
            assert result.success is False


class TestEmailVerification:
    """Test email verification."""

    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service, uow):
        """Email verification with valid token succeeds."""
        # Register with verification required
        reg = await auth_service.register(
            email="toverify@example.com",
            password="Password123!",
            display_name="To Verify",
            require_email_verification=True,
        )
        await uow.commit()

        assert reg.user.email_verified is False
        assert reg.verification_token is not None

        # Verify email
        result = await auth_service.verify_email(reg.verification_token)
        await uow.commit()

        assert result.success is True
        assert result.user is not None

        # Check user is now verified
        user = await uow.users.get_by_id(result.user.id)
        assert user.email_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, auth_service, uow):
        """Email verification with invalid token fails."""
        result = await auth_service.verify_email("invalid-token")

        assert result.success is False
        assert "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_resend_verification_email(self, auth_service, uow):
        """Resend verification generates new token."""
        # Register with verification required
        reg = await auth_service.register(
            email="resend@example.com",
            password="Password123!",
            display_name="Resend Test",
            require_email_verification=True,
        )
        await uow.commit()

        original_token = reg.verification_token

        # Resend
        success, new_token = await auth_service.resend_verification_email(
            "resend@example.com"
        )
        await uow.commit()

        assert success is True
        assert new_token is not None
        assert new_token != original_token

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(self, auth_service, test_user, uow):
        """Resend for verified user fails."""
        # test_user is created with require_email_verification=False (already verified)
        success, token = await auth_service.resend_verification_email(
            test_user["email"]
        )

        assert success is False
        assert token is None


class TestPasswordReset:
    """Test password reset functionality."""

    @pytest.mark.asyncio
    async def test_request_password_reset(self, auth_service, test_user, uow):
        """Request password reset generates token."""
        success, token = await auth_service.request_password_reset(
            test_user["email"]
        )
        await uow.commit()

        assert success is True
        assert token is not None

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_email(self, auth_service, uow):
        """Request reset for nonexistent email fails silently."""
        success, token = await auth_service.request_password_reset(
            "nonexistent@example.com"
        )

        assert success is False
        assert token is None

    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_service, test_user, uow):
        """Password reset with valid token succeeds."""
        # Request reset
        success, reset_token = await auth_service.request_password_reset(
            test_user["email"]
        )
        await uow.commit()

        new_password = "NewSecurePassword456!"

        # Reset password
        result = await auth_service.reset_password(reset_token, new_password)
        await uow.commit()

        assert result.success is True

        # Old password should no longer work
        old_login = await auth_service.login(
            email=test_user["email"],
            password=test_user["password"],
        )
        assert old_login.success is False

        # New password should work
        new_login = await auth_service.login(
            email=test_user["email"],
            password=new_password,
        )
        assert new_login.success is True

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, auth_service, uow):
        """Password reset with invalid token fails."""
        result = await auth_service.reset_password(
            "invalid-token",
            "NewPassword123!"
        )

        assert result.success is False
        assert "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_reset_password_revokes_all_tokens(self, auth_service, uow):
        """Password reset revokes all refresh tokens."""
        # Create user and login
        reg = await auth_service.register(
            email="resetall@example.com",
            password="OldPassword123!",
            display_name="Reset All",
            require_email_verification=False,
        )
        await uow.commit()

        login = await auth_service.login(
            email="resetall@example.com",
            password="OldPassword123!",
        )
        await uow.commit()

        refresh_token = login.tokens.refresh_token

        # Request and perform reset
        success, reset_token = await auth_service.request_password_reset(
            "resetall@example.com"
        )
        await uow.commit()

        await auth_service.reset_password(reset_token, "NewPassword456!")
        await uow.commit()

        # Old refresh token should not work
        result = await auth_service.refresh_tokens(refresh_token)
        assert result.success is False


class TestChangePassword:
    """Test password change for authenticated users."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, test_user, uow):
        """Authenticated password change succeeds."""
        # First login to get user id
        login = await auth_service.login(
            email=test_user["email"],
            password=test_user["password"],
        )
        await uow.commit()

        new_password = "ChangedPassword789!"

        result = await auth_service.change_password(
            user_id=login.user.id,
            current_password=test_user["password"],
            new_password=new_password,
        )
        await uow.commit()

        assert result.success is True

        # Old password should fail
        old_login = await auth_service.login(
            email=test_user["email"],
            password=test_user["password"],
        )
        assert old_login.success is False

        # New password should work
        new_login = await auth_service.login(
            email=test_user["email"],
            password=new_password,
        )
        assert new_login.success is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service, test_user, uow):
        """Password change with wrong current password fails."""
        login = await auth_service.login(
            email=test_user["email"],
            password=test_user["password"],
        )
        await uow.commit()

        result = await auth_service.change_password(
            user_id=login.user.id,
            current_password="WrongCurrent123!",
            new_password="NewPassword789!",
        )

        assert result.success is False
        assert "current password" in result.error.lower()

    @pytest.mark.asyncio
    async def test_change_password_nonexistent_user(self, auth_service, uow):
        """Password change for nonexistent user fails."""
        result = await auth_service.change_password(
            user_id=uuid.uuid4(),
            current_password="Whatever123!",
            new_password="NewPassword789!",
        )

        assert result.success is False
        assert "not found" in result.error.lower()
