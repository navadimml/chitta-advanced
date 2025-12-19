"""
Child Repository - Core Child Operations.

Handles child profile management and access checks.
The Child is the central entity around which all observations,
explorations, and synthesis revolve.
"""

import uuid
from datetime import datetime, timezone, date
from typing import Optional, List, Sequence

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models_core import Child
from app.db.models_access import FamilyMember, ChildAccess
from app.db.repositories.base import BaseRepository


class ChildRepository(BaseRepository[Child]):
    """Repository for Child operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Child, session)

    async def create_child(
        self,
        family_id: uuid.UUID,
        name: str,
        *,
        nickname: Optional[str] = None,
        birth_date: Optional[date] = None,
        gender: Optional[str] = None,
        **kwargs
    ) -> Child:
        """Create a new child in a family."""
        return await self.create(
            family_id=family_id,
            name=name,
            nickname=nickname,
            birth_date=birth_date,
            gender=gender,
            **kwargs
        )

    async def get_with_relations(
        self,
        child_id: uuid.UUID,
        *,
        load_observations: bool = False,
        load_explorations: bool = False,
        load_crystals: bool = False,
        load_sessions: bool = False
    ) -> Optional[Child]:
        """Get child with specified relations eagerly loaded."""
        relations = []
        if load_observations:
            relations.append("observations")
        if load_explorations:
            relations.append("explorations")
        if load_crystals:
            relations.append("crystals")
        if load_sessions:
            relations.append("sessions")

        return await self.get_by_id(child_id, load_relations=relations)

    async def get_family_children(
        self,
        family_id: uuid.UUID,
        *,
        include_deleted: bool = False
    ) -> Sequence[Child]:
        """Get all children in a family."""
        stmt = select(Child).where(Child.family_id == family_id)

        if not include_deleted:
            stmt = stmt.where(Child.deleted_at.is_(None))

        stmt = stmt.order_by(Child.created_at)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_accessible_children(
        self,
        user_id: uuid.UUID,
        *,
        include_deleted: bool = False
    ) -> Sequence[Child]:
        """
        Get all children accessible by a user.

        Includes children from:
        1. Families the user is a member of
        2. Children with direct child_access grants
        """
        now = datetime.now(timezone.utc)

        # Children from family membership
        family_children = select(Child).join(
            FamilyMember,
            Child.family_id == FamilyMember.family_id
        ).where(FamilyMember.user_id == user_id)

        # Children with direct access
        direct_children = select(Child).join(
            ChildAccess,
            Child.id == ChildAccess.child_id
        ).where(
            and_(
                ChildAccess.user_id == user_id,
                or_(
                    ChildAccess.expires_at.is_(None),
                    ChildAccess.expires_at > now
                )
            )
        )

        # Union both
        stmt = family_children.union(direct_children)

        if not include_deleted:
            # Note: deleted_at check applied to each select above would be cleaner
            pass  # Handle in individual queries if needed

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def can_user_access(
        self,
        user_id: uuid.UUID,
        child_id: uuid.UUID
    ) -> bool:
        """
        Check if user can access a child.

        Returns True if:
        1. User is a member of child's family, OR
        2. User has a valid child_access grant
        """
        child = await self.get_by_id(child_id)
        if not child:
            return False

        # Check family membership
        family_member = await self.session.execute(
            select(FamilyMember).where(
                and_(
                    FamilyMember.user_id == user_id,
                    FamilyMember.family_id == child.family_id
                )
            )
        )
        if family_member.scalar_one_or_none():
            return True

        # Check direct access
        now = datetime.now(timezone.utc)
        child_access = await self.session.execute(
            select(ChildAccess).where(
                and_(
                    ChildAccess.user_id == user_id,
                    ChildAccess.child_id == child_id,
                    or_(
                        ChildAccess.expires_at.is_(None),
                        ChildAccess.expires_at > now
                    )
                )
            )
        )
        return child_access.scalar_one_or_none() is not None

    async def get_user_access_type(
        self,
        user_id: uuid.UUID,
        child_id: uuid.UUID
    ) -> Optional[dict]:
        """
        Get details of how user accesses a child.

        Returns dict with:
        - access_type: 'family' or 'direct'
        - role: user's role
        - permissions: dict of permissions (for direct access)
        """
        child = await self.get_by_id(child_id)
        if not child:
            return None

        # Check family membership first
        family_member_result = await self.session.execute(
            select(FamilyMember).where(
                and_(
                    FamilyMember.user_id == user_id,
                    FamilyMember.family_id == child.family_id
                )
            )
        )
        family_member = family_member_result.scalar_one_or_none()

        if family_member:
            return {
                "access_type": "family",
                "role": family_member.role,
                "permissions": {
                    "can_chat": True,
                    "can_add_observations": True,
                    "can_view_parent_observations": True,
                    "can_view_conversations": True,
                    "can_view_crystals": True,
                    "can_add_clinical_notes": False,
                    "can_manage_access": family_member.role in ["owner", "parent"]
                }
            }

        # Check direct access
        now = datetime.now(timezone.utc)
        child_access_result = await self.session.execute(
            select(ChildAccess).where(
                and_(
                    ChildAccess.user_id == user_id,
                    ChildAccess.child_id == child_id,
                    or_(
                        ChildAccess.expires_at.is_(None),
                        ChildAccess.expires_at > now
                    )
                )
            )
        )
        child_access = child_access_result.scalar_one_or_none()

        if child_access:
            return {
                "access_type": "direct",
                "role": child_access.role,
                "permissions": {
                    "can_chat": child_access.can_chat,
                    "can_add_observations": child_access.can_add_observations,
                    "can_view_parent_observations": child_access.can_view_parent_observations,
                    "can_view_conversations": child_access.can_view_conversations,
                    "can_view_crystals": child_access.can_view_crystals,
                    "can_add_clinical_notes": child_access.can_add_clinical_notes,
                    "can_manage_access": False
                }
            }

        return None

    async def update_temporal_markers(
        self,
        child_id: uuid.UUID,
        *,
        last_observation_at: Optional[datetime] = None,
        last_crystal_at: Optional[datetime] = None,
        last_pattern_at: Optional[datetime] = None
    ) -> Optional[Child]:
        """Update temporal awareness markers on child."""
        updates = {}
        if last_observation_at:
            updates["last_observation_at"] = last_observation_at
        if last_crystal_at:
            updates["last_crystal_at"] = last_crystal_at
        if last_pattern_at:
            updates["last_pattern_at"] = last_pattern_at

        if updates:
            return await self.update(child_id, **updates)
        return await self.get_by_id(child_id)

    async def mark_intake_completed(self, child_id: uuid.UUID) -> Optional[Child]:
        """Mark intake as completed."""
        return await self.update(
            child_id,
            intake_completed_at=datetime.now(timezone.utc)
        )

    async def mark_baseline_completed(self, child_id: uuid.UUID) -> Optional[Child]:
        """Mark baseline assessment as completed."""
        return await self.update(
            child_id,
            baseline_completed_at=datetime.now(timezone.utc)
        )

    async def search_by_name(
        self,
        family_id: uuid.UUID,
        name_query: str,
        *,
        include_deleted: bool = False
    ) -> Sequence[Child]:
        """Search children by name within a family."""
        stmt = select(Child).where(
            and_(
                Child.family_id == family_id,
                or_(
                    Child.name.ilike(f"%{name_query}%"),
                    Child.nickname.ilike(f"%{name_query}%")
                )
            )
        )

        if not include_deleted:
            stmt = stmt.where(Child.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalars().all()
