"""
Family Service - Manages Family and User-Family relationships.

Now uses database persistence via UnitOfWork.
In-memory cache is maintained for performance but database is source of truth.

Design:
- Auto-creates Family + Child placeholder for new users
- Tracks user -> family -> children relationships
- Children are created as placeholders, identity filled via conversation
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict

from app.db.repositories import UnitOfWork
from app.db.base import UserRole

logger = logging.getLogger(__name__)


@dataclass
class ChildSummary:
    """Lightweight child info for family view."""
    id: str
    name: Optional[str] = None
    age_months: Optional[int] = None
    last_activity: Optional[datetime] = None


@dataclass
class Family:
    """Family entity - groups children under one parent."""
    id: str
    name: str = "המשפחה שלי"  # Default: "My Family"
    children: List[str] = field(default_factory=list)  # List of child_ids
    owner_user_id: Optional[str] = None
    preferred_language: str = "he"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserFamilyMapping:
    """Maps user to their family."""
    user_id: str
    family_id: str
    role: str = "owner"  # owner, parent, caregiver
    joined_at: datetime = field(default_factory=datetime.now)


class FamilyService:
    """
    Manages Families and their relationships to users and children.

    Uses database persistence via UnitOfWork.
    Maintains in-memory cache for performance.

    Key operations:
    - get_or_create_family_for_user: Auto-create family on first access
    - get_family_with_children: Get family + child summaries
    - add_child_to_family: Create a new child placeholder
    """

    def __init__(self):
        # In-memory caches (for performance, DB is source of truth)
        self._families: Dict[str, Family] = {}
        self._user_mappings: Dict[str, UserFamilyMapping] = {}  # user_id -> mapping
        logger.info("FamilyService initialized (database persistence enabled)")

    # === Core Operations ===

    async def get_or_create_family_for_user(
        self,
        user_id: str,
        uow: UnitOfWork,
        parent_type: Optional[str] = None
    ) -> Family:
        """
        Get user's family or create one if doesn't exist.

        For new users:
        1. Creates a new Family in database
        2. Creates a user->family mapping with parent_type as role
        3. Creates a child placeholder

        Args:
            user_id: User's ID
            uow: UnitOfWork for database operations
            parent_type: "mother" or "father" - used as role in family

        Returns the family.
        """
        # Convert UUID to string if necessary
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id
        user_uuid = uuid.UUID(user_id_str)

        # Check cache first
        if user_id_str in self._user_mappings:
            mapping = self._user_mappings[user_id_str]
            if mapping.family_id in self._families:
                return self._families[mapping.family_id]

        # Check database for existing family
        db_families = await uow.families.get_user_families(user_uuid)
        if db_families:
            # User already has a family - load it
            db_family = db_families[0]  # Take the first family
            family_id_str = str(db_family.id)

            # Get children from database
            db_children = await uow.children.get_family_children(db_family.id)
            child_ids = [str(child.id) for child in db_children]

            # Create local Family object
            family = Family(
                id=family_id_str,
                name=db_family.name,
                owner_user_id=user_id_str,
                children=child_ids,
                created_at=db_family.created_at,
                updated_at=db_family.updated_at or datetime.now(),
            )

            # Get user's role in family
            role = await uow.family_members.get_role(user_uuid, db_family.id)

            # Cache
            mapping = UserFamilyMapping(
                user_id=user_id_str,
                family_id=family_id_str,
                role=role or "owner",
            )
            self._families[family_id_str] = family
            self._user_mappings[user_id_str] = mapping

            logger.info(f"Loaded existing family {family_id_str} for user {user_id_str}")
            return family

        # New user - create everything in database
        logger.info(f"Creating new family for user: {user_id_str}")

        # Create family in database (this also adds owner as member)
        db_family = await uow.families.create_family(
            name="המשפחה שלי",
            owner_user_id=user_uuid,
        )
        family_id_str = str(db_family.id)

        # Create first child placeholder in database
        db_child = await uow.children.create_child(
            family_id=db_family.id,
            name="",  # Placeholder - identity filled via conversation
        )
        child_id_str = str(db_child.id)

        # Commit the transaction
        await uow.commit()

        # Create local Family object
        family = Family(
            id=family_id_str,
            owner_user_id=user_id_str,
            children=[child_id_str],
        )

        # Determine role
        role = parent_type if parent_type in ("mother", "father") else "owner"

        # Create user mapping
        mapping = UserFamilyMapping(
            user_id=user_id_str,
            family_id=family_id_str,
            role=role,
        )

        # Cache
        self._families[family_id_str] = family
        self._user_mappings[user_id_str] = mapping

        logger.info(f"Created family {family_id_str} with child {child_id_str} for user {user_id_str}")

        return family

    async def get_family_with_children(
        self,
        family_id: str,
        uow: UnitOfWork
    ) -> Dict[str, Any]:
        """
        Get family with child summaries for frontend display.

        Returns:
        {
            "family": { id, name },
            "children": [{ id, name, age_months, last_activity }]
        }
        """
        family = self._families.get(family_id)
        if not family:
            # Try loading from database
            family_uuid = uuid.UUID(family_id)
            db_family = await uow.families.get_by_id(family_uuid)
            if not db_family:
                raise ValueError(f"Family not found: {family_id}")

            db_children = await uow.children.get_family_children(family_uuid)
            child_ids = [str(child.id) for child in db_children]

            family = Family(
                id=family_id,
                name=db_family.name,
                children=child_ids,
            )
            self._families[family_id] = family

        # Get child summaries from database
        children_summaries = []
        for child_id in family.children:
            child_uuid = uuid.UUID(child_id)
            db_child = await uow.children.get_by_id(child_uuid)
            if db_child:
                summary = ChildSummary(
                    id=child_id,
                    name=db_child.name or None,
                    age_months=self._calculate_age_months_from_db(db_child),
                    last_activity=db_child.updated_at,
                )
                children_summaries.append(asdict(summary))

        return {
            "family": {
                "id": family.id,
                "name": family.name,
            },
            "children": children_summaries,
        }

    async def add_child_to_family(
        self,
        family_id: str,
        uow: UnitOfWork
    ) -> str:
        """
        Add a new child placeholder to family.

        Returns the new child_id.
        """
        family = self._families.get(family_id)
        if not family:
            family_uuid = uuid.UUID(family_id)
            db_family = await uow.families.get_by_id(family_uuid)
            if not db_family:
                raise ValueError(f"Family not found: {family_id}")

            # Load existing children
            db_children = await uow.children.get_family_children(family_uuid)
            child_ids = [str(child.id) for child in db_children]

            family = Family(
                id=family_id,
                name=db_family.name,
                children=child_ids,
            )
            self._families[family_id] = family

        # Create child in database
        family_uuid = uuid.UUID(family_id)
        db_child = await uow.children.create_child(
            family_id=family_uuid,
            name="",  # Placeholder
        )
        child_id_str = str(db_child.id)

        await uow.commit()

        # Update cache
        family.children.append(child_id_str)
        family.updated_at = datetime.now()

        logger.info(f"Added child {child_id_str} to family {family_id}")

        return child_id_str

    async def get_user_family_id(
        self,
        user_id: str,
        uow: Optional[UnitOfWork] = None
    ) -> Optional[str]:
        """Get the family_id for a user, without auto-creating."""
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id

        # Check cache
        mapping = self._user_mappings.get(user_id_str)
        if mapping:
            return mapping.family_id

        # Check database if uow provided
        if uow:
            user_uuid = uuid.UUID(user_id_str)
            db_families = await uow.families.get_user_families(user_uuid)
            if db_families:
                return str(db_families[0].id)

        return None

    async def get_family_children_ids(
        self,
        family_id: str,
        uow: Optional[UnitOfWork] = None
    ) -> List[str]:
        """Get list of child IDs in a family."""
        family = self._families.get(family_id)
        if family:
            return family.children.copy()

        # Check database if uow provided
        if uow:
            family_uuid = uuid.UUID(family_id)
            db_children = await uow.children.get_family_children(family_uuid)
            return [str(child.id) for child in db_children]

        return []

    async def user_has_access_to_child(
        self,
        user_id: str,
        child_id: str,
        uow: Optional[UnitOfWork] = None
    ) -> bool:
        """Check if user has access to a specific child via family membership."""
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id

        # Check cache
        mapping = self._user_mappings.get(user_id_str)
        if mapping:
            family = self._families.get(mapping.family_id)
            if family and child_id in family.children:
                return True

        # Check database if uow provided
        if uow:
            user_uuid = uuid.UUID(user_id_str)
            child_uuid = uuid.UUID(child_id)
            return await uow.children.can_user_access(user_uuid, child_uuid)

        return False

    async def get_user_role_in_family(
        self,
        user_id: str,
        family_id: str,
        uow: Optional[UnitOfWork] = None
    ) -> Optional[str]:
        """
        Get user's role in a family.

        Returns role: "mother", "father", "owner", "caregiver", etc.
        Returns None if user not in family.
        """
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id

        # Check cache
        mapping = self._user_mappings.get(user_id_str)
        if mapping and mapping.family_id == family_id:
            return mapping.role

        # Check database if uow provided
        if uow:
            user_uuid = uuid.UUID(user_id_str)
            family_uuid = uuid.UUID(family_id)
            return await uow.family_members.get_role(user_uuid, family_uuid)

        return None

    async def get_user_family_mapping(
        self,
        user_id: str,
        uow: Optional[UnitOfWork] = None
    ) -> Optional[UserFamilyMapping]:
        """
        Get the user's family mapping including role.

        Returns the full UserFamilyMapping or None.
        """
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id

        # Check cache
        mapping = self._user_mappings.get(user_id_str)
        if mapping:
            return mapping

        # Check database if uow provided
        if uow:
            user_uuid = uuid.UUID(user_id_str)
            db_families = await uow.families.get_user_families(user_uuid)
            if db_families:
                db_family = db_families[0]
                role = await uow.family_members.get_role(user_uuid, db_family.id)
                mapping = UserFamilyMapping(
                    user_id=user_id_str,
                    family_id=str(db_family.id),
                    role=role or "owner",
                )
                self._user_mappings[user_id_str] = mapping
                return mapping

        return None

    # === Private Helpers ===

    def _calculate_age_months_from_db(self, db_child) -> Optional[int]:
        """Calculate age in months from birth_date."""
        from datetime import date
        if not db_child.birth_date:
            return None

        today = date.today()
        birth = db_child.birth_date
        months = (today.year - birth.year) * 12 + (today.month - birth.month)
        if today.day < birth.day:
            months -= 1
        return max(0, months)


# Singleton
_family_service: Optional[FamilyService] = None


def get_family_service() -> FamilyService:
    """Get singleton FamilyService instance."""
    global _family_service
    if _family_service is None:
        _family_service = FamilyService()
    return _family_service
