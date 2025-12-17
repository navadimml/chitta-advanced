"""
Family Repository - Access Control Management.

Handles the three-tier access model:
- Layer 1: Family Members (parents, grandparents)
- Layer 2: Child Access (clinicians, specialists)
- Layer 3: Shared Artifacts (report sharing)

Also handles invitations for pending access grants.
"""

import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Sequence

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import UserRole, ChildAccessRole, InvitationStatus, ArtifactType
from app.db.models_access import (
    Family,
    FamilyMember,
    ChildAccess,
    SharedArtifact,
    Invitation,
)
from app.db.repositories.base import BaseRepository


class FamilyRepository(BaseRepository[Family]):
    """Repository for Family operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Family, session)

    async def create_family(
        self,
        name: str,
        owner_user_id: uuid.UUID,
        **kwargs
    ) -> Family:
        """
        Create a new family with owner.

        Automatically adds the creator as owner member.
        """
        family = await self.create(name=name, **kwargs)

        # Add owner as family member
        member = FamilyMember(
            user_id=owner_user_id,
            family_id=family.id,
            role=UserRole.OWNER.value,
            joined_at=datetime.now(timezone.utc)
        )
        self.session.add(member)
        await self.session.flush()

        return family

    async def get_user_families(
        self,
        user_id: uuid.UUID,
        *,
        include_deleted: bool = False
    ) -> Sequence[Family]:
        """Get all families a user belongs to."""
        stmt = select(Family).join(FamilyMember).where(
            FamilyMember.user_id == user_id
        )

        if not include_deleted:
            stmt = stmt.where(Family.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_members(
        self,
        family_id: uuid.UUID
    ) -> Optional[Family]:
        """Get family with members eagerly loaded."""
        return await self.get_by_id(
            family_id,
            load_relations=["members", "children"]
        )


class FamilyMemberRepository(BaseRepository[FamilyMember]):
    """Repository for Family Member operations (Layer 1 access)."""

    def __init__(self, session: AsyncSession):
        super().__init__(FamilyMember, session)

    async def get_membership(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID
    ) -> Optional[FamilyMember]:
        """Get user's membership in a family."""
        stmt = select(FamilyMember).where(
            and_(
                FamilyMember.user_id == user_id,
                FamilyMember.family_id == family_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_member(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID
    ) -> bool:
        """Check if user is a member of family."""
        membership = await self.get_membership(user_id, family_id)
        return membership is not None

    async def get_role(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID
    ) -> Optional[str]:
        """Get user's role in family."""
        membership = await self.get_membership(user_id, family_id)
        return membership.role if membership else None

    async def add_member(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        role: UserRole,
        invited_by: Optional[uuid.UUID] = None
    ) -> FamilyMember:
        """Add a member to family."""
        return await self.create(
            user_id=user_id,
            family_id=family_id,
            role=role.value,
            invited_by=invited_by,
            joined_at=datetime.now(timezone.utc)
        )

    async def update_role(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        new_role: UserRole
    ) -> Optional[FamilyMember]:
        """Update member's role."""
        membership = await self.get_membership(user_id, family_id)
        if not membership:
            return None
        membership.role = new_role.value
        await self.session.flush()
        return membership

    async def remove_member(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID
    ) -> bool:
        """Remove member from family."""
        membership = await self.get_membership(user_id, family_id)
        if not membership:
            return False
        await self.session.delete(membership)
        await self.session.flush()
        return True

    async def get_family_members(
        self,
        family_id: uuid.UUID
    ) -> Sequence[FamilyMember]:
        """Get all members of a family."""
        stmt = select(FamilyMember).where(
            FamilyMember.family_id == family_id
        ).options(selectinload(FamilyMember.user))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_owners(self, family_id: uuid.UUID) -> Sequence[FamilyMember]:
        """Get family owners."""
        stmt = select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.role == UserRole.OWNER.value
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ChildAccessRepository(BaseRepository[ChildAccess]):
    """Repository for Child Access operations (Layer 2 access)."""

    def __init__(self, session: AsyncSession):
        super().__init__(ChildAccess, session)

    async def get_access(
        self,
        user_id: uuid.UUID,
        child_id: uuid.UUID
    ) -> Optional[ChildAccess]:
        """Get user's access to a specific child."""
        stmt = select(ChildAccess).where(
            and_(
                ChildAccess.user_id == user_id,
                ChildAccess.child_id == child_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_access(
        self,
        user_id: uuid.UUID,
        child_id: uuid.UUID
    ) -> bool:
        """Check if user has active access to child."""
        access = await self.get_access(user_id, child_id)
        if not access:
            return False
        # Check expiration
        if access.expires_at and access.expires_at < datetime.utcnow():  # Naive for SQLite
            return False
        return True

    async def grant_access(
        self,
        user_id: uuid.UUID,
        child_id: uuid.UUID,
        role: ChildAccessRole,
        granted_by: uuid.UUID,
        *,
        can_chat: bool = True,
        can_add_observations: bool = True,
        can_view_parent_observations: bool = True,
        can_view_conversations: bool = False,
        can_view_crystals: bool = True,
        can_add_clinical_notes: bool = True,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None,
        organization: Optional[str] = None
    ) -> ChildAccess:
        """Grant child-specific access to a user (e.g., clinician)."""
        return await self.create(
            user_id=user_id,
            child_id=child_id,
            role=role.value,
            granted_by=granted_by,
            granted_at=datetime.now(timezone.utc),
            can_chat=can_chat,
            can_add_observations=can_add_observations,
            can_view_parent_observations=can_view_parent_observations,
            can_view_conversations=can_view_conversations,
            can_view_crystals=can_view_crystals,
            can_add_clinical_notes=can_add_clinical_notes,
            expires_at=expires_at,
            notes=notes,
            organization=organization
        )

    async def revoke_access(
        self,
        user_id: uuid.UUID,
        child_id: uuid.UUID
    ) -> bool:
        """Revoke child-specific access."""
        access = await self.get_access(user_id, child_id)
        if not access:
            return False
        await self.session.delete(access)
        await self.session.flush()
        return True

    async def get_child_clinicians(
        self,
        child_id: uuid.UUID
    ) -> Sequence[ChildAccess]:
        """Get all users with access to a child."""
        stmt = select(ChildAccess).where(
            ChildAccess.child_id == child_id
        ).options(selectinload(ChildAccess.user))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_children(
        self,
        user_id: uuid.UUID
    ) -> Sequence[ChildAccess]:
        """Get all children a user has access to (via child_access)."""
        now = datetime.now(timezone.utc)
        stmt = select(ChildAccess).where(
            and_(
                ChildAccess.user_id == user_id,
                or_(
                    ChildAccess.expires_at.is_(None),
                    ChildAccess.expires_at > now
                )
            )
        ).options(selectinload(ChildAccess.child))

        result = await self.session.execute(stmt)
        return result.scalars().all()


class SharedArtifactRepository(BaseRepository[SharedArtifact]):
    """Repository for Shared Artifact operations (Layer 3 access)."""

    def __init__(self, session: AsyncSession):
        super().__init__(SharedArtifact, session)

    async def share_artifact(
        self,
        artifact_type: ArtifactType,
        artifact_id: uuid.UUID,
        child_id: uuid.UUID,
        shared_by: uuid.UUID,
        *,
        shared_with_user_id: Optional[uuid.UUID] = None,
        shared_with_email: Optional[str] = None,
        create_link: bool = False,
        expires_in_days: Optional[int] = None,
        max_access_count: Optional[int] = None,
        message: Optional[str] = None
    ) -> SharedArtifact:
        """
        Share an artifact (crystal, report, etc.).

        Can share with:
        - Specific user (shared_with_user_id)
        - Email address (shared_with_email)
        - Public link (create_link=True)
        """
        share_token = None
        if create_link:
            share_token = secrets.token_urlsafe(32)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        return await self.create(
            artifact_type=artifact_type.value,
            artifact_id=artifact_id,
            child_id=child_id,
            shared_by=shared_by,
            shared_at=datetime.now(timezone.utc),
            shared_with_user_id=shared_with_user_id,
            shared_with_email=shared_with_email,
            share_token=share_token,
            expires_at=expires_at,
            max_access_count=max_access_count,
            message=message
        )

    async def get_by_token(self, token: str) -> Optional[SharedArtifact]:
        """Get shared artifact by share token."""
        return await self.get_by_field("share_token", token)

    async def get_valid_share(self, token: str) -> Optional[SharedArtifact]:
        """Get valid (not expired, not exceeded access count) shared artifact."""
        share = await self.get_by_token(token)
        if not share:
            return None
        if not share.is_valid:
            return None
        return share

    async def record_access(
        self,
        share_id: uuid.UUID,
        ip_address: Optional[str] = None
    ) -> None:
        """Record an access to a shared artifact."""
        share = await self.get_by_id(share_id)
        if share:
            share.access_count += 1
            share.last_accessed_at = datetime.now(timezone.utc)
            share.last_accessed_by_ip = ip_address
            await self.session.flush()

    async def get_artifact_shares(
        self,
        artifact_type: str,
        artifact_id: uuid.UUID
    ) -> Sequence[SharedArtifact]:
        """Get all shares for an artifact."""
        stmt = select(SharedArtifact).where(
            and_(
                SharedArtifact.artifact_type == artifact_type,
                SharedArtifact.artifact_id == artifact_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_received_shares(
        self,
        user_id: uuid.UUID
    ) -> Sequence[SharedArtifact]:
        """Get artifacts shared with a user."""
        now = datetime.now(timezone.utc)
        stmt = select(SharedArtifact).where(
            and_(
                SharedArtifact.shared_with_user_id == user_id,
                or_(
                    SharedArtifact.expires_at.is_(None),
                    SharedArtifact.expires_at > now
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def revoke_share(self, share_id: uuid.UUID) -> bool:
        """Revoke a share by deleting it."""
        return await self.delete(share_id, hard_delete=True)


class InvitationRepository(BaseRepository[Invitation]):
    """Repository for Invitation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Invitation, session)

    async def create_family_invitation(
        self,
        family_id: uuid.UUID,
        email: str,
        role: UserRole,
        invited_by: uuid.UUID,
        message: Optional[str] = None,
        expires_in_days: int = 7
    ) -> Invitation:
        """Create invitation to join a family."""
        token_hash = secrets.token_urlsafe(32)
        return await self.create(
            family_id=family_id,
            email=email.lower(),
            role=role.value,
            token_hash=token_hash,
            invited_by=invited_by,
            message=message,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        )

    async def create_child_invitation(
        self,
        child_id: uuid.UUID,
        email: str,
        role: ChildAccessRole,
        invited_by: uuid.UUID,
        message: Optional[str] = None,
        expires_in_days: int = 7
    ) -> Invitation:
        """Create invitation for child-specific access."""
        token_hash = secrets.token_urlsafe(32)
        return await self.create(
            child_id=child_id,
            email=email.lower(),
            role=role.value,
            token_hash=token_hash,
            invited_by=invited_by,
            message=message,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        )

    async def get_by_token(self, token_hash: str) -> Optional[Invitation]:
        """Get invitation by token."""
        return await self.get_by_field("token_hash", token_hash)

    async def get_pending_invitation(self, token_hash: str) -> Optional[Invitation]:
        """Get pending (not expired, not responded) invitation."""
        stmt = select(Invitation).where(
            and_(
                Invitation.token_hash == token_hash,
                Invitation.status == InvitationStatus.PENDING.value,
                Invitation.expires_at > datetime.utcnow()  # Naive for SQLite
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_for_email(self, email: str) -> Sequence[Invitation]:
        """Get all pending invitations for an email."""
        stmt = select(Invitation).where(
            and_(
                Invitation.email == email.lower(),
                Invitation.status == InvitationStatus.PENDING.value,
                Invitation.expires_at > datetime.utcnow()  # Naive for SQLite
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def accept(
        self,
        token_hash: str,
        accepted_by_user_id: uuid.UUID
    ) -> Optional[Invitation]:
        """Accept an invitation."""
        invitation = await self.get_pending_invitation(token_hash)
        if not invitation:
            return None

        invitation.status = InvitationStatus.ACCEPTED.value
        invitation.responded_at = datetime.now(timezone.utc)
        invitation.accepted_by_user_id = accepted_by_user_id
        await self.session.flush()
        return invitation

    async def decline(self, token_hash: str) -> Optional[Invitation]:
        """Decline an invitation."""
        invitation = await self.get_pending_invitation(token_hash)
        if not invitation:
            return None

        invitation.status = InvitationStatus.DECLINED.value
        invitation.responded_at = datetime.now(timezone.utc)
        await self.session.flush()
        return invitation

    async def get_family_invitations(
        self,
        family_id: uuid.UUID
    ) -> Sequence[Invitation]:
        """Get all invitations for a family."""
        return await self.get_many_by_field("family_id", family_id)

    async def get_child_invitations(
        self,
        child_id: uuid.UUID
    ) -> Sequence[Invitation]:
        """Get all invitations for child access."""
        return await self.get_many_by_field("child_id", child_id)
