"""
Family Service - Manages Family and User-Family relationships.

Note: Now uses in-memory storage only. Persistence is handled by Darshan.

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

    Note: Uses in-memory storage only. Persistence is handled by Darshan.

    Key operations:
    - get_or_create_family_for_user: Auto-create family on first access
    - get_family_with_children: Get family + child summaries
    - add_child_to_family: Create a new child placeholder
    """

    def __init__(self):
        # In-memory caches
        self._families: Dict[str, Family] = {}
        self._user_mappings: Dict[str, UserFamilyMapping] = {}  # user_id -> mapping
        logger.info("FamilyService initialized (in-memory, Darshan handles persistence)")

    # === Core Operations ===

    async def get_or_create_family_for_user(
        self,
        user_id: str,
        parent_type: Optional[str] = None
    ) -> Family:
        """
        Get user's family or create one if doesn't exist (in-memory).

        For new users:
        1. Creates a new Family
        2. Creates a user->family mapping with parent_type as role
        3. Creates a child placeholder

        Args:
            user_id: User's ID
            parent_type: "mother" or "father" - used as role in family

        Returns the family.
        """
        # Convert UUID to string if necessary
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id

        # Check cache first
        if user_id_str in self._user_mappings:
            mapping = self._user_mappings[user_id_str]
            if mapping.family_id in self._families:
                return self._families[mapping.family_id]

        # New user - create everything
        logger.info(f"Creating new family for user: {user_id_str}")

        # Create family
        family_id = str(uuid.uuid4())
        family = Family(
            id=family_id,
            owner_user_id=user_id_str,
            children=[],
        )

        # Create user mapping - use parent_type as role if provided
        role = parent_type if parent_type in ("mother", "father") else "owner"
        mapping = UserFamilyMapping(
            user_id=user_id_str,
            family_id=family_id,
            role=role,
        )

        # Create first child placeholder
        child_id = await self._create_child_placeholder(family_id)
        family.children.append(child_id)

        # Cache only (no file persistence)
        self._families[family_id] = family
        self._user_mappings[user_id_str] = mapping

        logger.info(f"Created family {family_id} with child {child_id} for user {user_id_str}")

        return family

    async def get_family_with_children(self, family_id: str) -> Dict[str, Any]:
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
            raise ValueError(f"Family not found: {family_id}")

        # Get child summaries
        from app.services.child_service import get_child_service
        child_service = get_child_service()

        children_summaries = []
        for child_id in family.children:
            child = child_service.get_or_create_child(child_id)
            summary = ChildSummary(
                id=child_id,
                name=child.identity.name,
                age_months=self._calculate_age_months(child),
                last_activity=child.updated_at,
            )
            children_summaries.append(asdict(summary))

        return {
            "family": {
                "id": family.id,
                "name": family.name,
            },
            "children": children_summaries,
        }

    async def add_child_to_family(self, family_id: str) -> str:
        """
        Add a new child placeholder to family.

        Returns the new child_id.
        """
        family = self._families.get(family_id)
        if not family:
            raise ValueError(f"Family not found: {family_id}")

        # Create child placeholder
        child_id = await self._create_child_placeholder(family_id)
        family.children.append(child_id)
        family.updated_at = datetime.now()

        logger.info(f"Added child {child_id} to family {family_id}")

        return child_id

    async def get_user_family_id(self, user_id: str) -> Optional[str]:
        """Get the family_id for a user, without auto-creating."""
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id
        mapping = self._user_mappings.get(user_id_str)
        return mapping.family_id if mapping else None

    async def get_family_children_ids(self, family_id: str) -> List[str]:
        """Get list of child IDs in a family."""
        family = self._families.get(family_id)
        if not family:
            return []
        return family.children.copy()

    async def user_has_access_to_child(self, user_id: str, child_id: str) -> bool:
        """Check if user has access to a specific child via family membership."""
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id
        mapping = self._user_mappings.get(user_id_str)
        if not mapping:
            return False

        family = self._families.get(mapping.family_id)
        if not family:
            return False

        return child_id in family.children

    async def get_user_role_in_family(self, user_id: str, family_id: str) -> Optional[str]:
        """
        Get user's role in a family.

        Returns role: "mother", "father", "owner", "caregiver", etc.
        Returns None if user not in family.
        """
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id
        mapping = self._user_mappings.get(user_id_str)
        if not mapping or mapping.family_id != family_id:
            return None
        return mapping.role

    async def get_user_family_mapping(self, user_id: str) -> Optional[UserFamilyMapping]:
        """
        Get the user's family mapping including role.

        Returns the full UserFamilyMapping or None.
        """
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id
        return self._user_mappings.get(user_id_str)

    # === Private Helpers ===

    async def _create_child_placeholder(self, family_id: str) -> str:
        """Create a new child with no identity (placeholder)."""
        from app.services.child_service import get_child_service
        child_service = get_child_service()

        # Generate child ID
        child_id = str(uuid.uuid4())

        # Create child through child service
        child_service.get_or_create_child(child_id)

        logger.info(f"Created child placeholder: {child_id} for family {family_id}")

        return child_id

    def _calculate_age_months(self, child) -> Optional[int]:
        """Calculate age in months from birth_date."""
        from datetime import date
        if not child.identity.birth_date:
            return None

        today = date.today()
        birth = child.identity.birth_date
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
