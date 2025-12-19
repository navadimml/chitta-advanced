"""
Child Space Service - Daniel's Space artifact management.

Part of Living Dashboard Phase 2: Manages the "Living Header" / "Memory Drawer"
that provides quick access to all artifacts for a child.

This service:
1. Reads slot configuration from artifacts.yaml
2. Populates slots with current artifact data from FamilyState
3. Provides slot summaries for header badges
4. Handles slot history for versioned artifacts
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.config.config_loader import load_artifacts
from app.models.artifact_slot import (
    ArtifactSlot,
    SlotItem,
    ChildSpace,
    create_slot_from_config,
    create_slot_item_from_artifact,
)
from app.models.family_state import FamilyState

logger = logging.getLogger(__name__)


class ChildSpaceService:
    """
    Service for managing Daniel's Space - the artifact slot system.

    Provides:
    - get_child_space(): Full space with all slots for UI rendering
    - get_header_summary(): Compact badges for header display
    - get_slot_detail(): Detailed slot info including history
    """

    def __init__(self):
        self._artifacts_config = load_artifacts()
        self._slots_config = self._artifacts_config.get("slots", {})
        self._slot_order = self._artifacts_config.get("slot_order", [])
        self._artifacts = self._artifacts_config.get("artifacts", {})

        # Build artifact-to-slot mapping
        self._artifact_to_slot: Dict[str, str] = {}
        for artifact_id, artifact_config in self._artifacts.items():
            slot_config = artifact_config.get("slot", {})
            if slot_id := slot_config.get("slot_id"):
                self._artifact_to_slot[artifact_id] = slot_id

        logger.info(
            f"ChildSpaceService initialized: "
            f"{len(self._slots_config)} slots, "
            f"{len(self._artifact_to_slot)} artifact-slot mappings"
        )

    def get_child_space(self, family_state: FamilyState) -> ChildSpace:
        """
        Get the complete Child Space for UI rendering.

        Args:
            family_state: Current family state with artifacts

        Returns:
            ChildSpace with all slots populated
        """
        # Create slots in configured order
        slots = []
        for slot_id in self._slot_order:
            slot_config = self._slots_config.get(slot_id)
            if not slot_config:
                logger.warning(f"Slot {slot_id} in slot_order but not in slots config")
                continue

            # Include history so the UI can show the history button
            slot = self._build_slot(slot_id, slot_config, family_state, include_history=True)
            slots.append(slot)

        # Build header badges
        header_badges = self._build_header_badges(slots)

        # Get child name
        child_name = None
        if family_state.child:
            child_name = family_state.child.get("name")

        return ChildSpace(
            family_id=family_state.family_id,
            child_name=child_name,
            slots=slots,
            header_badges=header_badges,
            last_updated=datetime.utcnow(),
        )

    def get_header_summary(self, family_state: FamilyState) -> List[Dict[str, str]]:
        """
        Get compact header badges for the Living Header.

        Returns only slots that have content, for display as pills/badges.

        Args:
            family_state: Current family state

        Returns:
            List of badge dicts: [{"icon": "📄", "text": "Report Ready", "slot_id": "..."}]
        """
        space = self.get_child_space(family_state)
        return space.header_badges

    def get_slot_detail(
        self,
        family_state: FamilyState,
        slot_id: str
    ) -> Optional[ArtifactSlot]:
        """
        Get detailed information for a specific slot.

        Includes full history for versioned slots.

        Args:
            family_state: Current family state
            slot_id: Slot to get details for

        Returns:
            ArtifactSlot with full details, or None if not found
        """
        slot_config = self._slots_config.get(slot_id)
        if not slot_config:
            return None

        return self._build_slot(slot_id, slot_config, family_state, include_history=True)

    def get_slot_for_artifact(self, artifact_id: str) -> Optional[str]:
        """
        Get the slot ID that an artifact belongs to.

        Args:
            artifact_id: Artifact identifier

        Returns:
            Slot ID or None if artifact has no slot
        """
        return self._artifact_to_slot.get(artifact_id)

    def _build_slot(
        self,
        slot_id: str,
        slot_config: Dict[str, Any],
        family_state: FamilyState,
        include_history: bool = False
    ) -> ArtifactSlot:
        """
        Build an ArtifactSlot populated with current data.

        Args:
            slot_id: Slot identifier
            slot_config: Slot configuration from YAML
            family_state: Current family state
            include_history: Whether to include version history

        Returns:
            Populated ArtifactSlot
        """
        slot = create_slot_from_config(slot_id, slot_config)

        # Find artifacts that belong to this slot
        slot_artifacts = self._get_artifacts_for_slot(slot_id, family_state)

        if slot.is_collection:
            # Collection slot (videos, journal)
            self._populate_collection_slot(slot, slot_artifacts, family_state)
        else:
            # Single-item slot (report, guidelines)
            self._populate_single_slot(slot, slot_artifacts, include_history)

        # Update computed state
        slot.has_content = slot.current is not None or slot.item_count > 0
        slot.last_updated = self._get_slot_last_updated(slot)
        slot.badge_text = self._get_badge_text(slot)

        return slot

    def _get_artifacts_for_slot(
        self,
        slot_id: str,
        family_state: FamilyState
    ) -> List[Dict[str, Any]]:
        """
        Get all artifacts that belong to a slot.

        Also finds versioned artifacts (e.g., baseline_parent_report_v1, _v2)
        that belong to the same slot as the base artifact.

        Args:
            slot_id: Slot identifier
            family_state: Current family state

        Returns:
            List of artifact data dicts
        """
        import re
        artifacts = []

        # Get base artifact IDs for this slot
        base_artifact_ids = [
            artifact_id for artifact_id, slot in self._artifact_to_slot.items()
            if slot == slot_id
        ]

        # Check all artifacts in family state
        for artifact_id, artifact_data in family_state.artifacts.items():
            # Check if this artifact belongs to this slot
            # Either by exact match or by being a versioned variant (_v0, _v1, etc.)
            belongs_to_slot = False
            base_config = {}

            if artifact_id in base_artifact_ids:
                # Exact match
                belongs_to_slot = True
                base_config = self._artifacts.get(artifact_id, {})
            else:
                # Check if it's a versioned variant (e.g., baseline_parent_report_v1)
                for base_id in base_artifact_ids:
                    if re.match(rf"^{re.escape(base_id)}_v\d+$", artifact_id):
                        belongs_to_slot = True
                        base_config = self._artifacts.get(base_id, {})
                        break

            if belongs_to_slot:
                artifacts.append({
                    "artifact_id": artifact_id,
                    "config": base_config,
                    "data": self._normalize_artifact_data(artifact_data),
                })

        return artifacts

    def _normalize_artifact_data(self, artifact_data: Any) -> Dict[str, Any]:
        """Normalize artifact data to a dict."""
        if hasattr(artifact_data, "model_dump"):
            return artifact_data.model_dump()
        elif isinstance(artifact_data, dict):
            return artifact_data
        else:
            return {"status": "unknown"}

    def _populate_collection_slot(
        self,
        slot: ArtifactSlot,
        slot_artifacts: List[Dict[str, Any]],
        family_state: FamilyState
    ) -> None:
        """
        Populate a collection slot (videos, journal).

        Args:
            slot: Slot to populate
            slot_artifacts: Artifacts belonging to this slot
            family_state: Family state for additional data
        """
        # For videos, count from family_state.videos_uploaded
        if slot.slot_id == "videos":
            videos = family_state.videos_uploaded or []
            slot.item_count = len(videos)

            if videos:
                latest = videos[-1]
                slot.latest_item = SlotItem(
                    artifact_id=latest.id,
                    artifact_type="video",
                    name=latest.scenario or "Video",
                    status="ready",
                    created_at=latest.uploaded_at,
                    duration_seconds=latest.duration_seconds,
                )
                slot.current = slot.latest_item

        # For journal, count from family_state.journal_entries
        elif slot.slot_id == "journal":
            entries = family_state.journal_entries or []
            slot.item_count = len(entries)

            if entries:
                latest = entries[-1]
                slot.latest_item = SlotItem(
                    artifact_id=latest.id,
                    artifact_type="journal",
                    name="Journal Entry",
                    status="saved",
                    created_at=latest.timestamp,
                    preview=latest.content[:100] if latest.content else None,
                )
                slot.current = slot.latest_item

    def _populate_single_slot(
        self,
        slot: ArtifactSlot,
        slot_artifacts: List[Dict[str, Any]],
        include_history: bool
    ) -> None:
        """
        Populate a single-item slot (report, guidelines).

        Args:
            slot: Slot to populate
            slot_artifacts: Artifacts belonging to this slot
            include_history: Whether to include version history
        """
        if not slot_artifacts:
            return

        # Sort by created_at descending (newest first)
        slot_artifacts.sort(
            key=lambda a: a["data"].get("created_at") or datetime.min,
            reverse=True
        )

        # Current is the newest
        newest = slot_artifacts[0]
        slot.current = create_slot_item_from_artifact(
            artifact_id=newest["artifact_id"],
            artifact_config=newest["config"],
            artifact_data=newest["data"],
        )

        # Update slot state based on current artifact
        slot.is_generating = slot.current.status == "generating"
        slot.has_error = slot.current.status == "error"

        # Include history if requested
        if include_history and len(slot_artifacts) > 1:
            for artifact in slot_artifacts[1:]:
                history_item = create_slot_item_from_artifact(
                    artifact_id=artifact["artifact_id"],
                    artifact_config=artifact["config"],
                    artifact_data=artifact["data"],
                )
                slot.history.append(history_item)

    def _get_slot_last_updated(self, slot: ArtifactSlot) -> Optional[datetime]:
        """Get the most recent update time for a slot."""
        if slot.current and slot.current.updated_at:
            return slot.current.updated_at
        if slot.current and slot.current.created_at:
            return slot.current.created_at
        if slot.latest_item and slot.latest_item.created_at:
            return slot.latest_item.created_at
        return None

    def _get_badge_text(self, slot: ArtifactSlot) -> Optional[str]:
        """Get badge text for slot display."""
        if slot.is_generating:
            return "מכין..."  # Generating...

        if slot.has_error:
            return "שגיאה"  # Error

        if slot.is_collection:
            if slot.item_count == 0:
                return None
            elif slot.item_count == 1:
                return "1"
            else:
                return str(slot.item_count)

        if slot.current:
            if slot.current.status == "ready":
                return "מוכן"  # Ready
            elif slot.current.status == "generating":
                return "מכין..."

        return None

    def _build_header_badges(self, slots: List[ArtifactSlot]) -> List[Dict[str, str]]:
        """
        Build header badges from populated slots.

        Only includes slots with content.
        """
        badges = []

        for slot in slots:
            if not slot.has_content:
                continue

            badge = {
                "slot_id": slot.slot_id,
                "icon": slot.icon,
                "text": slot.badge_text or slot.slot_name,
            }

            # Add status indicator
            if slot.is_generating:
                badge["status"] = "generating"
            elif slot.has_error:
                badge["status"] = "error"
            elif slot.current and slot.current.status == "ready":
                badge["status"] = "ready"

            badges.append(badge)

        return badges


# Global singleton
_child_space_service: Optional[ChildSpaceService] = None


def get_child_space_service() -> ChildSpaceService:
    """Get global ChildSpaceService instance."""
    global _child_space_service
    if _child_space_service is None:
        _child_space_service = ChildSpaceService()
    return _child_space_service
