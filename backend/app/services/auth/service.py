"""
Authentication Service.

High-level authentication operations:
- User registration
- Login (email/password and OAuth)
- Token refresh
- Logout
- Password management
- Email verification
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from dataclasses import dataclass

from app.db.repositories import UnitOfWork
from app.db.models_auth import User
from app.db.base import AuditAction

from app.services.auth.config import get_auth_settings
from app.services.auth.password import hash_password, verify_password, needs_rehash
from app.services.auth.tokens import (
    TokenService,
    TokenPair,
    TokenPayload,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    get_token_service,
)


@dataclass
class AuthResult:
    """Result of authentication operation."""
    success: bool
    user: Optional[User] = None
    tokens: Optional[TokenPair] = None
    error: Optional[str] = None
    requires_verification: bool = False


@dataclass
class RegistrationResult:
    """Result of user registration."""
    success: bool
    user: Optional[User] = None
    verification_token: Optional[str] = None
    error: Optional[str] = None


class AuthError(Exception):
    """Base authentication error."""
    pass


class InvalidCredentialsError(AuthError):
    """Invalid email or password."""
    pass


class AccountLockedError(AuthError):
    """Account is locked due to too many failed attempts."""
    pass


class AccountDisabledError(AuthError):
    """Account is disabled."""
    pass


class EmailNotVerifiedError(AuthError):
    """Email address not verified."""
    pass


class EmailAlreadyExistsError(AuthError):
    """Email already registered."""
    pass


class TokenReuseError(AuthError):
    """Refresh token was reused (possible theft)."""
    pass


class AuthService:
    """
    Service for authentication operations.

    Usage:
        async with UnitOfWork() as uow:
            auth = AuthService(uow)

            # Register
            result = await auth.register(
                email="user@example.com",
                password="securepass123",
                display_name="Test User"
            )

            # Login
            result = await auth.login(
                email="user@example.com",
                password="securepass123"
            )

            # Refresh
            result = await auth.refresh_tokens(refresh_token)

            await uow.commit()
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.settings = get_auth_settings()
        self.token_service = get_token_service()

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
        *,
        parent_type: Optional[str] = None,
        require_email_verification: bool = True,
        ip_address: Optional[str] = None,
    ) -> RegistrationResult:
        """
        Register a new user.

        Args:
            email: User's email address
            password: Plain text password
            display_name: Display name
            parent_type: Parent type - "mother" or "father"
            require_email_verification: Whether to require email verification
            ip_address: IP address for audit log

        Returns:
            RegistrationResult with user and optional verification token
        """
        # Check if email exists
        existing = await self.uow.users.get_by_email(email)
        if existing:
            return RegistrationResult(
                success=False,
                error="Email already registered"
            )

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = await self.uow.users.create_user(
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            email_verified=not require_email_verification,
            parent_type=parent_type,
        )

        # Create verification token if needed
        verification_token = None
        if require_email_verification:
            plain_token, token_hash = self.token_service.generate_verification_token()
            await self.uow.email_tokens.create_token(
                user_id=user.id,
                email=email,
                token_hash=token_hash,
                expires_in_hours=self.settings.email_verification_expire_hours
            )
            verification_token = plain_token

        # Audit log
        await self.uow.audit_log.log(
            action=AuditAction.LOGIN,  # Using LOGIN for now, could add REGISTER
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            ip_address=ip_address,
            details=f"User registered: {email}"
        )

        return RegistrationResult(
            success=True,
            user=user,
            verification_token=verification_token
        )

    # =========================================================================
    # LOGIN
    # =========================================================================

    async def login(
        self,
        email: str,
        password: str,
        *,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_name: Optional[str] = None,
        require_verified_email: bool = True,
    ) -> AuthResult:
        """
        Authenticate user with email and password.

        Args:
            email: User's email
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent
            device_name: Optional device name
            require_verified_email: Require email to be verified

        Returns:
            AuthResult with user and tokens on success
        """
        # Find user
        user = await self.uow.users.get_by_email(email)

        if not user:
            # Don't reveal that email doesn't exist
            return AuthResult(
                success=False,
                error="Invalid email or password"
            )

        # Check if account is locked (use utcnow for SQLite compatibility)
        if user.locked_until and user.locked_until > datetime.utcnow():
            await self._log_failed_login(user.id, ip_address, "Account locked")
            return AuthResult(
                success=False,
                error="Account is temporarily locked. Please try again later."
            )

        # Check if account is active
        if not user.is_active:
            await self._log_failed_login(user.id, ip_address, "Account disabled")
            return AuthResult(
                success=False,
                error="Account is disabled"
            )

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            # Record failed attempt
            attempts = await self.uow.users.record_failed_login(
                user.id,
                max_attempts=self.settings.max_login_attempts,
                lockout_minutes=self.settings.lockout_duration_minutes
            )
            await self._log_failed_login(user.id, ip_address, "Invalid password")
            return AuthResult(
                success=False,
                error="Invalid email or password"
            )

        # Check email verification
        if require_verified_email and not user.email_verified:
            return AuthResult(
                success=False,
                error="Please verify your email address",
                requires_verification=True
            )

        # Check if password needs rehash
        if user.password_hash and needs_rehash(user.password_hash):
            new_hash = hash_password(password)
            await self.uow.users.change_password(user.id, new_hash)

        # Create tokens
        tokens, family, token_hash = self.token_service.create_token_pair(user.id)

        # Store refresh token
        await self.uow.refresh_tokens.create_token(
            user_id=user.id,
            token_hash=token_hash,
            token_family=family,
            expires_at=tokens.refresh_token_expires,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Record successful login
        await self.uow.users.record_login(user.id, ip_address)

        # Audit log
        await self.uow.audit_log.log(
            action=AuditAction.LOGIN,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

        return AuthResult(
            success=True,
            user=user,
            tokens=tokens
        )

    async def _log_failed_login(
        self,
        user_id: uuid.UUID,
        ip_address: Optional[str],
        reason: str
    ) -> None:
        """Log failed login attempt."""
        await self.uow.audit_log.log(
            action=AuditAction.LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            success=False,
            failure_reason=reason
        )

    # =========================================================================
    # TOKEN REFRESH
    # =========================================================================

    async def refresh_tokens(
        self,
        refresh_token: str,
        *,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthResult:
        """
        Refresh access token using refresh token.

        Implements token rotation:
        - Old refresh token is revoked
        - New refresh token is issued with same family
        - If token reuse detected, entire family is revoked

        Args:
            refresh_token: Current refresh token
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            AuthResult with new tokens
        """
        try:
            # Verify token structure
            payload = self.token_service.verify_refresh_token(refresh_token)
        except TokenExpiredError:
            return AuthResult(success=False, error="Refresh token expired")
        except TokenInvalidError as e:
            return AuthResult(success=False, error=str(e))

        # Get token hash
        token_hash = self.token_service.get_token_hash(refresh_token)

        # Find stored token
        stored_token = await self.uow.refresh_tokens.get_by_token_hash(token_hash)

        if not stored_token:
            # Token not found - might be reuse of old token
            # Revoke entire family as security measure
            if payload.family:
                await self.uow.refresh_tokens.revoke_family(uuid.UUID(payload.family))
            return AuthResult(
                success=False,
                error="Invalid refresh token"
            )

        # Check if already revoked (token reuse attack!)
        if stored_token.revoked_at:
            # Someone is reusing an old token - revoke entire family
            await self.uow.refresh_tokens.revoke_family(stored_token.token_family)
            await self.uow.audit_log.log(
                action=AuditAction.LOGOUT,  # Security event
                user_id=stored_token.user_id,
                ip_address=ip_address,
                success=False,
                failure_reason="Refresh token reuse detected - all sessions revoked"
            )
            return AuthResult(
                success=False,
                error="Session invalidated for security. Please login again."
            )

        # Check expiration (use utcnow for SQLite compatibility)
        if stored_token.expires_at < datetime.utcnow():
            return AuthResult(success=False, error="Refresh token expired")

        # Get user
        user = await self.uow.users.get_by_id(stored_token.user_id)
        if not user or not user.is_active:
            return AuthResult(success=False, error="User not found or disabled")

        # Revoke old token
        await self.uow.refresh_tokens.revoke_token(token_hash)

        # Create new token pair with same family
        new_tokens, _, new_token_hash = self.token_service.create_token_pair(
            user.id,
            token_family=stored_token.token_family
        )

        # Store new refresh token
        await self.uow.refresh_tokens.create_token(
            user_id=user.id,
            token_hash=new_token_hash,
            token_family=stored_token.token_family,
            expires_at=new_tokens.refresh_token_expires,
            device_name=stored_token.device_name,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return AuthResult(
            success=True,
            user=user,
            tokens=new_tokens
        )

    # =========================================================================
    # LOGOUT
    # =========================================================================

    async def logout(
        self,
        refresh_token: str,
        *,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Logout by revoking refresh token.

        Args:
            refresh_token: Token to revoke
            ip_address: Client IP

        Returns:
            True if successful
        """
        token_hash = self.token_service.get_token_hash(refresh_token)
        result = await self.uow.refresh_tokens.revoke_token(token_hash)

        if result:
            # Try to get user_id for audit
            try:
                payload = self.token_service.decode_token_unverified(refresh_token)
                user_id = uuid.UUID(payload.get("sub"))
                await self.uow.audit_log.log(
                    action=AuditAction.LOGOUT,
                    user_id=user_id,
                    ip_address=ip_address,
                    success=True
                )
            except Exception:
                pass

        return result

    async def logout_all_devices(
        self,
        user_id: uuid.UUID,
        *,
        ip_address: Optional[str] = None,
    ) -> int:
        """
        Logout from all devices by revoking all refresh tokens.

        Args:
            user_id: User to logout
            ip_address: Client IP

        Returns:
            Number of tokens revoked
        """
        count = await self.uow.refresh_tokens.revoke_all_user_tokens(user_id)

        await self.uow.audit_log.log(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            ip_address=ip_address,
            details=f"Logged out from all devices ({count} sessions)"
        )

        return count

    # =========================================================================
    # EMAIL VERIFICATION
    # =========================================================================

    async def verify_email(
        self,
        token: str,
        *,
        ip_address: Optional[str] = None,
    ) -> AuthResult:
        """
        Verify email address using token.

        Args:
            token: Verification token (plain, not hash)
            ip_address: Client IP

        Returns:
            AuthResult with user on success
        """
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Find valid token
        stored_token = await self.uow.email_tokens.get_valid_token(token_hash)

        if not stored_token:
            return AuthResult(
                success=False,
                error="Invalid or expired verification token"
            )

        # Mark token as used
        await self.uow.email_tokens.mark_used(token_hash)

        # Verify user email
        await self.uow.users.verify_email(stored_token.user_id)

        # Get user
        user = await self.uow.users.get_by_id(stored_token.user_id)

        return AuthResult(
            success=True,
            user=user
        )

    async def resend_verification_email(
        self,
        email: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Generate new verification token.

        Args:
            email: User's email

        Returns:
            Tuple of (success, verification_token)
        """
        user = await self.uow.users.get_by_email(email)

        if not user:
            return False, None

        if user.email_verified:
            return False, None

        # Generate new token
        plain_token, token_hash = self.token_service.generate_verification_token()
        await self.uow.email_tokens.create_token(
            user_id=user.id,
            email=email,
            token_hash=token_hash,
            expires_in_hours=self.settings.email_verification_expire_hours
        )

        return True, plain_token

    # =========================================================================
    # PASSWORD RESET
    # =========================================================================

    async def request_password_reset(
        self,
        email: str,
        *,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Request password reset.

        Args:
            email: User's email
            ip_address: Client IP

        Returns:
            Tuple of (user_exists, reset_token)
            Note: Always behave the same whether user exists or not
        """
        user = await self.uow.users.get_by_email(email)

        if not user:
            # Don't reveal that user doesn't exist
            return False, None

        # Generate reset token
        plain_token, token_hash = self.token_service.generate_verification_token()
        await self.uow.password_tokens.create_token(
            user_id=user.id,
            token_hash=token_hash,
            ip_address=ip_address,
            expires_in_hours=self.settings.password_reset_expire_hours
        )

        return True, plain_token

    async def reset_password(
        self,
        token: str,
        new_password: str,
        *,
        ip_address: Optional[str] = None,
    ) -> AuthResult:
        """
        Reset password using token.

        Args:
            token: Reset token (plain, not hash)
            new_password: New password
            ip_address: Client IP

        Returns:
            AuthResult with user on success
        """
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Find valid token
        stored_token = await self.uow.password_tokens.get_valid_token(token_hash)

        if not stored_token:
            return AuthResult(
                success=False,
                error="Invalid or expired reset token"
            )

        # Mark token as used
        await self.uow.password_tokens.mark_used(token_hash)

        # Hash new password
        password_hash = hash_password(new_password)

        # Update password
        await self.uow.users.change_password(stored_token.user_id, password_hash)

        # Revoke all refresh tokens (force re-login everywhere)
        await self.uow.refresh_tokens.revoke_all_user_tokens(stored_token.user_id)

        # Get user
        user = await self.uow.users.get_by_id(stored_token.user_id)

        # Audit
        await self.uow.audit_log.log(
            action=AuditAction.LOGIN,  # Could add PASSWORD_RESET action
            user_id=stored_token.user_id,
            ip_address=ip_address,
            details="Password reset completed"
        )

        return AuthResult(
            success=True,
            user=user
        )

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
        *,
        ip_address: Optional[str] = None,
    ) -> AuthResult:
        """
        Change password (authenticated user).

        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password
            ip_address: Client IP

        Returns:
            AuthResult
        """
        user = await self.uow.users.get_by_id(user_id)

        if not user or not user.password_hash:
            return AuthResult(success=False, error="User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return AuthResult(success=False, error="Current password is incorrect")

        # Hash and update
        new_hash = hash_password(new_password)
        await self.uow.users.change_password(user_id, new_hash)

        # Audit
        await self.uow.audit_log.log(
            action=AuditAction.LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            details="Password changed"
        )

        return AuthResult(success=True, user=user)
