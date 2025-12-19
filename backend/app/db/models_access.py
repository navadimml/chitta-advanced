"""
Access Layer Models - Three-tier access control.

Layer 1: Family Members - Full family access (parents, grandparents)
Layer 2: Child Access - Child-specific access (clinicians, therapists)
Layer 3: Shared Artifacts - One-time or limited sharing (reports, crystals)

Also includes:
- Families (logical grouping of children)
- Invitations (pending access grants)
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    UserRole,
    ChildAccessRole,
    ArtifactType,
    InvitationStatus,
)

if TYPE_CHECKING:
    from app.db.models_auth import User
    from app.db.models_core import Child


class Family(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Family - a logical grouping of children.

    A family can have multiple children and multiple members.
    Members access all children in the family based on their role.
    """

    __tablename__ = "families"

    # Identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "משפחת כהן"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Settings
    preferred_language: Mapped[str] = mapped_column(String(5), default="he", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Jerusalem", nullable=False)

    # Subscription/billing (for future)
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    members: Mapped[List["FamilyMember"]] = relationship(
        "FamilyMember", back_populates="family", cascade="all, delete-orphan"
    )
    children: Mapped[List["Child"]] = relationship(
        "Child", back_populates="family", cascade="all, delete-orphan"
    )
    invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation", back_populates="family", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Family {self.name}>"


class FamilyMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Layer 1: Family-level access.

    Links users to families with role-based permissions.
    Members see ALL children in the family.
    """

    __tablename__ = "family_members"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="CASCADE"), nullable=False
    )

    # Role determines permissions
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # UserRole enum

    # Tracking
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Notification preferences
    notify_new_observations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_new_crystals: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_milestones: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="family_memberships", foreign_keys=[user_id])
    family: Mapped["Family"] = relationship("Family", back_populates="members")
    inviter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        Index("ix_family_member_unique", "user_id", "family_id", unique=True),
        Index("ix_family_member_family", "family_id"),
    )

    def __repr__(self) -> str:
        return f"<FamilyMember user={self.user_id} family={self.family_id} role={self.role}>"


class ChildAccess(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Layer 2: Child-specific access.

    For clinicians, therapists, specialists who only need access to specific children.
    Does NOT grant access to siblings or family-level data.
    """

    __tablename__ = "child_access"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Role
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # ChildAccessRole enum

    # Granular permissions
    can_chat: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_add_observations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_view_parent_observations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_view_conversations: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_view_crystals: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_add_clinical_notes: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Grant tracking
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Context
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # "יועל - קלינאית תקשורת"
    organization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # "מרכז שניידר"

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="child_access_grants", foreign_keys=[user_id])
    child: Mapped["Child"] = relationship("Child", back_populates="access_grants")
    granter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[granted_by])

    __table_args__ = (
        Index("ix_child_access_unique", "user_id", "child_id", unique=True),
        Index("ix_child_access_child", "child_id"),
    )

    @property
    def is_active(self) -> bool:
        if self.expires_at is None:
            return True
        return self.expires_at > datetime.utcnow()

    def __repr__(self) -> str:
        return f"<ChildAccess user={self.user_id} child={self.child_id} role={self.role}>"


class SharedArtifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Layer 3: Artifact-level sharing.

    For sharing specific reports, crystals, or analyses.
    Can be shared with specific users, via email, or via public link.
    """

    __tablename__ = "shared_artifacts"

    # What is being shared
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ArtifactType enum
    artifact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Who shared it
    shared_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Access method (one of these should be set)
    shared_with_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    shared_with_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    share_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)

    # Access control
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_access_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Tracking
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_accessed_by_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Optional message from sharer
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="shared_artifacts")
    sharer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[shared_by])
    recipient: Mapped[Optional["User"]] = relationship("User", foreign_keys=[shared_with_user_id])

    __table_args__ = (
        Index("ix_shared_artifact_child", "child_id"),
        Index("ix_shared_artifact_token", "share_token"),
        Index("ix_shared_artifact_type_id", "artifact_type", "artifact_id"),
    )

    @property
    def is_valid(self) -> bool:
        """Check if share is still valid."""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        return True

    def __repr__(self) -> str:
        return f"<SharedArtifact {self.artifact_type}:{self.artifact_id}>"


class Invitation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Pending invitations to join a family or access a child.

    Sent via email before the invitee has an account.
    """

    __tablename__ = "invitations"

    # Target (family or child)
    family_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="CASCADE"), nullable=True
    )
    child_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=True
    )

    # Invitee
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # UserRole or ChildAccessRole

    # Invitation details
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Personal message from inviter

    # Inviter
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # InvitationStatus
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # If accepted, the user that was created/linked
    accepted_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    family: Mapped[Optional["Family"]] = relationship("Family", back_populates="invitations")
    child: Mapped[Optional["Child"]] = relationship("Child", back_populates="invitations")
    inviter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[invited_by])
    accepted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[accepted_by_user_id])

    __table_args__ = (
        Index("ix_invitation_email_status", "email", "status"),
        Index("ix_invitation_family", "family_id"),
        Index("ix_invitation_child", "child_id"),
    )

    @property
    def is_pending(self) -> bool:
        return self.status == InvitationStatus.PENDING.value and self.expires_at > datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Invitation {self.email} -> family={self.family_id} child={self.child_id}>"
