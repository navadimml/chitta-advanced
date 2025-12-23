"""
Family Service - Manages Family and User-Family relationships.

Follows the same file-storage pattern as ChildService.

Design:
- Auto-creates Family + Child placeholder for new users
- Tracks user -> family -> children relationships
- Children are created as placeholders, identity filled via conversation
"""

import logging
import json
import os
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# Storage configuration
STORAGE_TYPE = os.getenv("FAMILY_STORAGE_TYPE", os.getenv("SESSION_STORAGE_TYPE", "file"))
DATA_DIR = os.getenv("FAMILY_DATA_DIR", "data/families")

# Ensure data directory exists
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


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

    Key operations:
    - get_or_create_family_for_user: Auto-create family on first access
    - get_family_with_children: Get family + child summaries
    - add_child_to_family: Create a new child placeholder
    """

    def __init__(self):
        # In-memory caches
        self._families: Dict[str, Family] = {}
        self._user_mappings: Dict[str, UserFamilyMapping] = {}  # user_id -> mapping

        # Storage type
        self._storage_type = STORAGE_TYPE

        logger.info(f"FamilyService initialized with {self._storage_type} storage")

    def _get_family_file_path(self, family_id: str) -> Path:
        """Get file path for a family's data."""
        safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in family_id)
        return Path(DATA_DIR) / f"family_{safe_id}.json"

    def _get_user_mapping_file_path(self, user_id) -> Path:
        """Get file path for user->family mapping."""
        # Convert UUID to string if necessary
        user_id_str = str(user_id) if hasattr(user_id, 'hex') else user_id
        safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in user_id_str)
        return Path(DATA_DIR) / f"user_mapping_{safe_id}.json"

    # === Core Operations ===

    async def get_or_create_family_for_user(
        self,
        user_id: str,
        parent_type: Optional[str] = None
    ) -> Family:
        """
        Get user's family or create one if doesn't exist.

        For new users:
        1. Creates a new Family
        2. Creates a user->family mapping with parent_type as role
        3. Creates a child placeholder

        Args:
            user_id: User's ID
            parent_type: "mother" or "father" - used as role in family

        Returns the family.
        """
        # Check cache first
        if user_id in self._user_mappings:
            mapping = self._user_mappings[user_id]
            family = await self._get_family(mapping.family_id)
            if family:
                return family

        # Try to load from storage
        mapping = await self._load_user_mapping(user_id)
        if mapping:
            self._user_mappings[user_id] = mapping
            family = await self._get_family(mapping.family_id)
            if family:
                return family

        # New user - create everything
        logger.info(f"Creating new family for user: {user_id}")

        # Create family
        family_id = str(uuid.uuid4())
        family = Family(
            id=family_id,
            owner_user_id=user_id,
            children=[],
        )

        # Create user mapping - use parent_type as role if provided
        role = parent_type if parent_type in ("mother", "father") else "owner"
        mapping = UserFamilyMapping(
            user_id=user_id,
            family_id=family_id,
            role=role,
        )

        # Create first child placeholder
        child_id = await self._create_child_placeholder(family_id)
        family.children.append(child_id)

        # Cache and persist
        self._families[family_id] = family
        self._user_mappings[user_id] = mapping

        await self._save_family(family)
        await self._save_user_mapping(mapping)

        logger.info(f"Created family {family_id} with child {child_id} for user {user_id}")

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
        family = await self._get_family(family_id)
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
        family = await self._get_family(family_id)
        if not family:
            raise ValueError(f"Family not found: {family_id}")

        # Create child placeholder
        child_id = await self._create_child_placeholder(family_id)
        family.children.append(child_id)
        family.updated_at = datetime.now()

        await self._save_family(family)

        logger.info(f"Added child {child_id} to family {family_id}")

        return child_id

    async def get_user_family_id(self, user_id: str) -> Optional[str]:
        """Get the family_id for a user, without auto-creating."""
        # Check cache
        if user_id in self._user_mappings:
            return self._user_mappings[user_id].family_id

        # Try to load
        mapping = await self._load_user_mapping(user_id)
        if mapping:
            self._user_mappings[user_id] = mapping
            return mapping.family_id

        return None

    async def get_family_children_ids(self, family_id: str) -> List[str]:
        """Get list of child IDs in a family."""
        family = await self._get_family(family_id)
        if not family:
            return []
        return family.children.copy()

    async def user_has_access_to_child(self, user_id: str, child_id: str) -> bool:
        """Check if user has access to a specific child via family membership."""
        mapping = self._user_mappings.get(user_id)
        if not mapping:
            mapping = await self._load_user_mapping(user_id)
            if mapping:
                self._user_mappings[user_id] = mapping

        if not mapping:
            return False

        family = await self._get_family(mapping.family_id)
        if not family:
            return False

        return child_id in family.children

    async def get_user_role_in_family(self, user_id: str, family_id: str) -> Optional[str]:
        """
        Get user's role in a family.

        Returns role: "mother", "father", "owner", "caregiver", etc.
        Returns None if user not in family.
        """
        mapping = self._user_mappings.get(user_id)
        if not mapping:
            mapping = await self._load_user_mapping(user_id)
            if mapping:
                self._user_mappings[user_id] = mapping

        if not mapping or mapping.family_id != family_id:
            return None

        return mapping.role

    async def get_user_family_mapping(self, user_id: str) -> Optional[UserFamilyMapping]:
        """
        Get the user's family mapping including role.

        Returns the full UserFamilyMapping or None.
        """
        mapping = self._user_mappings.get(user_id)
        if not mapping:
            mapping = await self._load_user_mapping(user_id)
            if mapping:
                self._user_mappings[user_id] = mapping
        return mapping

    # === Private Helpers ===

    async def _get_family(self, family_id: str) -> Optional[Family]:
        """Get family from cache or load from storage."""
        if family_id in self._families:
            return self._families[family_id]

        family = await self._load_family(family_id)
        if family:
            self._families[family_id] = family

        return family

    async def _create_child_placeholder(self, family_id: str) -> str:
        """Create a new child with no identity (placeholder)."""
        from app.services.child_service import get_child_service
        child_service = get_child_service()

        # Generate child ID
        child_id = str(uuid.uuid4())

        # Create child through child service
        child = child_service.get_or_create_child(child_id)

        # Save it
        await child_service.save_child(child_id)

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

    # === Storage Operations ===

    async def _load_family(self, family_id: str) -> Optional[Family]:
        """Load family from file storage."""
        file_path = self._get_family_file_path(family_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert datetime strings back
            if "created_at" in data and isinstance(data["created_at"], str):
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            if "updated_at" in data and isinstance(data["updated_at"], str):
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])

            return Family(**data)
        except Exception as e:
            logger.error(f"Error loading family {family_id}: {e}")
            return None

    async def _save_family(self, family: Family) -> bool:
        """Save family to file storage."""
        file_path = self._get_family_file_path(family.id)
        try:
            data = asdict(family)
            # Convert datetime to string for JSON
            data["created_at"] = family.created_at.isoformat()
            data["updated_at"] = family.updated_at.isoformat()

            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path.rename(file_path)

            logger.debug(f"Saved family to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving family {family.id}: {e}")
            return False

    async def _load_user_mapping(self, user_id: str) -> Optional[UserFamilyMapping]:
        """Load user->family mapping from file."""
        file_path = self._get_user_mapping_file_path(user_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert datetime
            if "joined_at" in data and isinstance(data["joined_at"], str):
                data["joined_at"] = datetime.fromisoformat(data["joined_at"])

            return UserFamilyMapping(**data)
        except Exception as e:
            logger.error(f"Error loading user mapping {user_id}: {e}")
            return None

    async def _save_user_mapping(self, mapping: UserFamilyMapping) -> bool:
        """Save user mapping to file."""
        file_path = self._get_user_mapping_file_path(mapping.user_id)
        try:
            data = asdict(mapping)
            data["joined_at"] = mapping.joined_at.isoformat()

            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path.rename(file_path)

            logger.debug(f"Saved user mapping to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving user mapping {mapping.user_id}: {e}")
            return False


# Singleton
_family_service: Optional[FamilyService] = None


def get_family_service() -> FamilyService:
    """Get singleton FamilyService instance."""
    global _family_service
    if _family_service is None:
        _family_service = FamilyService()
    return _family_service
