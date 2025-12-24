"""
Authentication and Authorization Models.

Includes:
- Users (core identity)
- OAuth accounts (Google, Apple, etc.)
- Refresh tokens (JWT rotation)
- Email verification and password reset tokens
- Audit log for security tracking
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    AuditAction,
)


class UserRole(str, Enum):
    """User roles in the system."""
    PARENT = "parent"           # Primary user - parents of children
    CLINICIAN = "clinician"     # Clinical professionals (therapists, pediatricians)
    RESEARCHER = "researcher"   # Research team members
    ADMIN = "admin"             # System administrators

if TYPE_CHECKING:
    from app.db.models_access import FamilyMember, ChildAccess
    from app.db.models_core import Session


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Core user identity.

    Users authenticate via email/password or OAuth.
    They access children through family membership or direct child access grants.
    """

    __tablename__ = "users"

    # Identity
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Profile
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(5), default="he", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Jerusalem", nullable=False)

    # Role-based access
    role: Mapped[str] = mapped_column(String(20), default=UserRole.PARENT.value, nullable=False)
    parent_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "אמא" or "אבא" (only for parent role)

    # Auth (nullable if OAuth-only user)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Security
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 max length

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    family_memberships: Mapped[List["FamilyMember"]] = relationship(
        "FamilyMember", back_populates="user", foreign_keys="FamilyMember.user_id"
    )
    child_access_grants: Mapped[List["ChildAccess"]] = relationship(
        "ChildAccess", back_populates="user", foreign_keys="ChildAccess.user_id"
    )
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="user"
    )

    # Indexes
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    @property
    def can_access_dashboard(self) -> bool:
        """Check if user can access the team dashboard."""
        return self.role in [UserRole.CLINICIAN.value, UserRole.RESEARCHER.value, UserRole.ADMIN.value] or self.is_admin

    @property
    def is_clinical_expert(self) -> bool:
        """Check if user is a clinical expert (clinician or researcher)."""
        return self.role in [UserRole.CLINICIAN.value, UserRole.RESEARCHER.value]


class OAuthAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    OAuth provider accounts linked to users.

    Supports multiple providers per user (Google + Apple, etc.)
    """

    __tablename__ = "oauth_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # 'google', 'apple', 'facebook'
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Token storage (encrypted in production)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        Index("ix_oauth_provider_user", "provider", "provider_user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<OAuthAccount {self.provider}:{self.provider_user_id}>"


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    JWT refresh tokens with rotation support.

    Implements secure token rotation:
    - Each refresh creates a new token
    - Old tokens are revoked
    - Token families track rotation chains
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Token identification
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA-256 hash
    token_family: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # Links rotation chain

    # Validity
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Device info
    device_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'mobile', 'desktop', 'tablet'
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_token_user_active", "user_id", "revoked_at"),
        Index("ix_refresh_token_family", "token_family"),
    )

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.utcnow()

    def __repr__(self) -> str:
        return f"<RefreshToken user={self.user_id} valid={self.is_valid}>"


class EmailVerificationToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tokens for email verification."""

    __tablename__ = "email_verification_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)  # Email being verified
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_email_verify_user", "user_id"),
    )


class PasswordResetToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tokens for password reset."""

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    __table_args__ = (
        Index("ix_password_reset_user", "user_id"),
    )


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    Security audit log.

    Tracks important actions for compliance and debugging.
    Immutable - no updates or deletes.
    """

    __tablename__ = "audit_log"

    # When
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Who
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # What
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # AuditAction enum value
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'child', 'family', etc.
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Details
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON for extra context
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_audit_user_time", "user_id", "timestamp"),
        Index("ix_audit_action_time", "action", "timestamp"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id} at {self.timestamp}>"
