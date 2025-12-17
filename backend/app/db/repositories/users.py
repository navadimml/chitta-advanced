"""
User Repository - Authentication and User Management.

Handles:
- User CRUD operations
- OAuth account management
- Refresh token management
- Email verification and password reset tokens
- Audit logging
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Sequence

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AuditAction
from app.db.models_auth import (
    User,
    OAuthAccount,
    RefreshToken,
    EmailVerificationToken,
    PasswordResetToken,
    AuditLog,
)
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(
        self,
        email: str,
        *,
        include_deleted: bool = False
    ) -> Optional[User]:
        """Get user by email address."""
        stmt = select(User).where(User.email == email.lower())

        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_email(self, email: str) -> Optional[User]:
        """Get active (not locked, not deleted) user by email."""
        stmt = select(User).where(
            and_(
                User.email == email.lower(),
                User.deleted_at.is_(None),
                User.is_active == True,
                or_(
                    User.locked_until.is_(None),
                    User.locked_until < datetime.utcnow()  # Naive for SQLite compatibility
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        display_name: str,
        password_hash: Optional[str] = None,
        **kwargs
    ) -> User:
        """Create a new user."""
        return await self.create(
            email=email.lower(),
            display_name=display_name,
            password_hash=password_hash,
            **kwargs
        )

    async def record_login(
        self,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None
    ) -> None:
        """Record successful login."""
        await self.update(
            user_id,
            last_login_at=datetime.now(timezone.utc),
            last_login_ip=ip_address,
            failed_login_attempts=0,
            locked_until=None
        )

    async def record_failed_login(
        self,
        user_id: uuid.UUID,
        max_attempts: int = 5,
        lockout_minutes: int = 30
    ) -> int:
        """
        Record failed login attempt.

        Returns the new failed attempt count.
        Locks account if max attempts exceeded.
        """
        user = await self.get_by_id(user_id)
        if not user:
            return 0

        new_count = user.failed_login_attempts + 1
        updates = {"failed_login_attempts": new_count}

        if new_count >= max_attempts:
            updates["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)

        await self.update(user_id, **updates)
        return new_count

    async def change_password(
        self,
        user_id: uuid.UUID,
        new_password_hash: str
    ) -> bool:
        """Change user password."""
        result = await self.update(
            user_id,
            password_hash=new_password_hash,
            password_changed_at=datetime.now(timezone.utc)
        )
        return result is not None

    async def verify_email(self, user_id: uuid.UUID) -> bool:
        """Mark user email as verified."""
        result = await self.update(user_id, email_verified=True)
        return result is not None


class OAuthAccountRepository(BaseRepository[OAuthAccount]):
    """Repository for OAuth account operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(OAuthAccount, session)

    async def get_by_provider(
        self,
        provider: str,
        provider_user_id: str
    ) -> Optional[OAuthAccount]:
        """Get OAuth account by provider and provider user ID."""
        stmt = select(OAuthAccount).where(
            and_(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_accounts(self, user_id: uuid.UUID) -> Sequence[OAuthAccount]:
        """Get all OAuth accounts for a user."""
        return await self.get_many_by_field("user_id", user_id)

    async def link_account(
        self,
        user_id: uuid.UUID,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> OAuthAccount:
        """Link OAuth account to user."""
        return await self.create(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at
        )

    async def update_tokens(
        self,
        id: uuid.UUID,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> Optional[OAuthAccount]:
        """Update OAuth tokens."""
        updates = {"access_token": access_token}
        if refresh_token:
            updates["refresh_token"] = refresh_token
        if token_expires_at:
            updates["token_expires_at"] = token_expires_at
        return await self.update(id, **updates)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)

    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_valid_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get valid (not revoked, not expired) refresh token."""
        # Use utcnow() for SQLite compatibility (SQLite doesn't preserve timezone)
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        token_family: uuid.UUID,
        expires_at: datetime,
        device_name: Optional[str] = None,
        device_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RefreshToken:
        """Create a new refresh token."""
        return await self.create(
            user_id=user_id,
            token_hash=token_hash,
            token_family=token_family,
            expires_at=expires_at,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        token = await self.get_by_token_hash(token_hash)
        if not token:
            return False
        token.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def revoke_family(self, token_family: uuid.UUID) -> int:
        """Revoke all tokens in a family (security: token reuse detected)."""
        return await self.update_many(
            {"token_family": token_family},
            revoked_at=datetime.now(timezone.utc)
        )

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        """Revoke all tokens for a user (logout everywhere)."""
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()

        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now

        await self.session.flush()
        return len(tokens)

    async def cleanup_expired(self, older_than_days: int = 30) -> int:
        """Delete expired tokens older than specified days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        return await self.delete_many(
            {"expires_at": cutoff},  # This needs a custom implementation
            hard_delete=True
        )


class EmailVerificationTokenRepository(BaseRepository[EmailVerificationToken]):
    """Repository for email verification tokens."""

    def __init__(self, session: AsyncSession):
        super().__init__(EmailVerificationToken, session)

    async def get_valid_token(self, token_hash: str) -> Optional[EmailVerificationToken]:
        """Get valid (not used, not expired) verification token."""
        stmt = select(EmailVerificationToken).where(
            and_(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > datetime.utcnow()  # Naive for SQLite
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_token(
        self,
        user_id: uuid.UUID,
        email: str,
        token_hash: str,
        expires_in_hours: int = 24
    ) -> EmailVerificationToken:
        """Create email verification token."""
        return await self.create(
            user_id=user_id,
            email=email,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        )

    async def mark_used(self, token_hash: str) -> bool:
        """Mark token as used."""
        token = await self.get_by_field("token_hash", token_hash)
        if not token:
            return False
        token.used_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """Repository for password reset tokens."""

    def __init__(self, session: AsyncSession):
        super().__init__(PasswordResetToken, session)

    async def get_valid_token(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Get valid (not used, not expired) reset token."""
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.utcnow()  # Naive for SQLite
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        ip_address: Optional[str] = None,
        expires_in_hours: int = 1
    ) -> PasswordResetToken:
        """Create password reset token."""
        return await self.create(
            user_id=user_id,
            token_hash=token_hash,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        )

    async def mark_used(self, token_hash: str) -> bool:
        """Mark token as used."""
        token = await self.get_by_field("token_hash", token_hash)
        if not token:
            return False
        token.used_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for audit log operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def log(
        self,
        action: AuditAction,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None
    ) -> AuditLog:
        """Create audit log entry."""
        return await self.create(
            action=action.value,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )

    async def get_user_activity(
        self,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[AuditLog]:
        """Get audit log for a user."""
        stmt = select(AuditLog).where(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_resource_activity(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        limit: int = 100
    ) -> Sequence[AuditLog]:
        """Get audit log for a resource."""
        stmt = select(AuditLog).where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )
        ).order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()
