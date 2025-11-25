"""
Artifact Slot Model - Daniel's Space UI representation.

Part of Living Dashboard Phase 2: Slots provide quick access to artifacts
in a persistent, organized UI (the "Living Header" / "Memory Drawer").

Each slot represents a category of artifacts (report, guidelines, videos, journal)
and shows the "current" version with access to history.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class SlotItem(BaseModel):
    """
    An artifact instance within a slot.

    For single-item slots (report, guidelines): This is the current artifact.
    For collection slots (videos, journal): One item in the collection.
    """
    artifact_id: str
    artifact_type: str
    name: str
    name_en: Optional[str] = None

    # State
    status: str = "pending"  # pending, generating, ready, error
    version: int = 1

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Preview content (for quick display in slot card)
    preview: Optional[str] = None

    # For videos: duration, thumbnail
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None


class ArtifactSlot(BaseModel):
    """
    A slot in Daniel's Space.

    Slots are the UI containers that hold artifacts. They provide:
    - Quick visual access to artifact status
    - Actions (view, download, upload)
    - History for versioned artifacts
    - Collection summary for multi-item slots
    """
    # Identity (from config)
    slot_id: str
    slot_name: str
    slot_name_en: Optional[str] = None
    icon: str
    description: Optional[str] = None

    # Current state
    current: Optional[SlotItem] = None  # Current/latest artifact

    # For collections (videos, journal)
    is_collection: bool = False
    item_count: int = 0
    latest_item: Optional[SlotItem] = None

    # History (for versioned single-item slots)
    history: List[SlotItem] = Field(default_factory=list)

    # Actions available
    primary_action: Optional[str] = None
    secondary_action: Optional[str] = None

    # Computed state
    has_content: bool = False
    is_generating: bool = False
    has_error: bool = False

    # Display metadata
    last_updated: Optional[datetime] = None
    badge_text: Optional[str] = None  # e.g., "3 videos", "Ready", "Generating..."


class ChildSpace(BaseModel):
    """
    Daniel's Space - the complete artifact view for a child.

    This is returned by the API and rendered in the header/drawer.
    """
    # Child identity
    family_id: str
    child_name: Optional[str] = None
    child_photo_url: Optional[str] = None

    # All slots in display order
    slots: List[ArtifactSlot] = Field(default_factory=list)

    # Summary badges for header pills
    # e.g., [{"icon": "📄", "text": "Report Ready"}, {"icon": "📹", "text": "3 Videos"}]
    header_badges: List[Dict[str, str]] = Field(default_factory=list)

    # Metadata
    last_updated: Optional[datetime] = None


def create_slot_from_config(slot_id: str, slot_config: Dict[str, Any]) -> ArtifactSlot:
    """
    Factory function to create an ArtifactSlot from YAML config.

    Args:
        slot_id: The slot identifier
        slot_config: Slot configuration from artifacts.yaml

    Returns:
        ArtifactSlot instance (empty, ready to be populated with artifacts)
    """
    return ArtifactSlot(
        slot_id=slot_id,
        slot_name=slot_config.get("slot_name", slot_id),
        slot_name_en=slot_config.get("slot_name_en"),
        icon=slot_config.get("icon", "📁"),
        description=slot_config.get("description"),
        is_collection=slot_config.get("is_collection", False),
        primary_action=slot_config.get("primary_action"),
        secondary_action=slot_config.get("secondary_action"),
    )


def create_slot_item_from_artifact(
    artifact_id: str,
    artifact_config: Dict[str, Any],
    artifact_data: Optional[Dict[str, Any]] = None
) -> SlotItem:
    """
    Factory function to create a SlotItem from artifact config and data.

    Args:
        artifact_id: The artifact identifier
        artifact_config: Artifact configuration from artifacts.yaml
        artifact_data: Runtime artifact data (status, content, etc.)

    Returns:
        SlotItem instance
    """
    data = artifact_data or {}

    # Extract preview if configured
    preview = None
    slot_config = artifact_config.get("slot", {})
    preview_field = slot_config.get("preview_field")

    if preview_field and artifact_data:
        content = data.get("content", {})
        if isinstance(content, dict):
            preview = content.get(preview_field)
        elif isinstance(content, str) and len(content) < 200:
            preview = content

    return SlotItem(
        artifact_id=artifact_id,
        artifact_type=artifact_config.get("type", "unknown"),
        name=artifact_config.get("name", artifact_id),
        name_en=artifact_config.get("name_en"),
        status=data.get("status", "pending"),
        version=data.get("version", 1),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        preview=preview,
    )
