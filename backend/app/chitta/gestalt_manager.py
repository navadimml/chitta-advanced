"""
Gestalt Manager - Darshan Lifecycle & Persistence

Manages the lifecycle of Darshan instances:
- Loading from persistence (child files + session data)
- Detecting session transitions (>4 hour gaps)
- Memory distillation on session transitions
- Persisting state to files

Philosophy:
- Darshan is the observing intelligence
- State is preserved across sessions
- Memory is distilled when sessions transition
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .gestalt import Darshan
from .models import ConversationMemory

logger = logging.getLogger(__name__)


class GestaltManager:
    """
    Manages Darshan lifecycle: loading, caching, transition detection, persistence.
    """

    SESSION_GAP_HOURS = 4  # Hours that define a session transition

    def __init__(self, child_service, session_service):
        """
        Initialize GestaltManager with required services.

        Args:
            child_service: Service for child data persistence
            session_service: Service for session data persistence
        """
        self._child_service = child_service
        self._session_service = session_service
        self._gestalts: Dict[str, Darshan] = {}

    async def get_darshan_with_transition_check(self, family_id: str) -> Darshan:
        """
        Get Darshan, handling session transition if needed.

        Session transition occurs when:
        - Previous session exists AND
        - Gap > 4 hours since last message

        On transition:
        - Distill previous session into memory
        - Start new session with memory context
        """
        # Check cache first
        if family_id in self._gestalts:
            darshan = self._gestalts[family_id]
            if not self._is_session_transition(darshan):
                return darshan

        # Load child (returns Child object or creates new one)
        child = await self._child_service.get_or_create_child_async(family_id)

        # Get or create session (using SessionService properly)
        session = await self._session_service.get_or_create_session_async(family_id)

        # Build Darshan from persisted data
        # Extract data from our own persistence (gestalt files)
        child_data = self._extract_child_data_for_darshan(child, family_id)

        # Session history from child_data (persisted with Darshan state)
        session_history = child_data.get("session_history", [])

        # Get child's birth date for temporal calculations
        child_birth_date = None
        if hasattr(child, 'identity') and child.identity and child.identity.birth_date:
            child_birth_date = child.identity.birth_date

        darshan = Darshan.from_child_data(
            child_id=family_id,
            child_name=child.name or child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            # Read from old key for backwards compatibility with data files
            explorations_data=child_data.get("exploration_cycles") or child_data.get("explorations"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            # Read from old key for backwards compatibility with data files
            curiosities_data=child_data.get("curiosity_engine") or child_data.get("curiosities"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
            shared_summaries_data=child_data.get("shared_summaries"),
            child_birth_date=child_birth_date,
            session_flags_data=child_data.get("session_flags"),
        )

        # Cache it
        self._gestalts[family_id] = darshan

        return darshan

    async def get_darshan(self, family_id: str) -> Optional[Darshan]:
        """Get Darshan without transition check."""
        if family_id in self._gestalts:
            return self._gestalts[family_id]

        # Try to load child - returns Child object
        child = await self._child_service.get_or_create_child_async(family_id)

        # Get or create session
        session = await self._session_service.get_or_create_session_async(family_id)

        # Extract data from our persistence
        child_data = self._extract_child_data_for_darshan(child, family_id)

        # Session history from child_data (persisted with Darshan state)
        session_history = child_data.get("session_history", [])

        # Get child's birth date for temporal calculations
        child_birth_date = None
        if hasattr(child, 'identity') and child.identity and child.identity.birth_date:
            child_birth_date = child.identity.birth_date

        darshan = Darshan.from_child_data(
            child_id=family_id,
            child_name=child.name or child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            # Read from old key for backwards compatibility with data files
            explorations_data=child_data.get("exploration_cycles") or child_data.get("explorations"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            # Read from old key for backwards compatibility with data files
            curiosities_data=child_data.get("curiosity_engine") or child_data.get("curiosities"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
            shared_summaries_data=child_data.get("shared_summaries"),
            child_birth_date=child_birth_date,
            session_flags_data=child_data.get("session_flags"),
        )

        # Cache it
        self._gestalts[family_id] = darshan
        return darshan

    def _extract_child_data_for_darshan(self, child, family_id: str = None) -> Dict[str, Any]:
        """Extract data from Child model or file in format expected by Darshan.

        Args:
            child: Child model (may be empty if gestalt file format differs)
            family_id: The family_id to use for file lookup (fallback if child.id fails)
        """
        # Try to load from gestalt file using child.id first, then family_id as fallback
        # This handles seeded gestalt data which doesn't have child_id field
        file_id = getattr(child, 'id', None) or family_id
        if not file_id:
            logger.warning("No file_id available for gestalt loading")
            return self._empty_darshan_data()

        gestalt_file = Path("data/children") / f"{file_id}.json"
        if gestalt_file.exists():
            try:
                with open(gestalt_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded gestalt data for {file_id} from file")
                    return data
            except Exception as e:
                logger.warning(f"Failed to load gestalt file for {file_id}: {e}")

        # Otherwise return empty state - will be built through conversation
        return self._empty_darshan_data()

    def _empty_darshan_data(self) -> Dict[str, Any]:
        """Return empty Darshan state for new conversations."""
        return {
            "understanding": None,
            "explorations": [],
            "stories": [],
            "journal": [],
            "curiosities": None,
        }

    def _is_session_transition(self, darshan: Darshan) -> bool:
        """Check if enough time has passed to consider this a new session."""
        if not darshan.session_history:
            return False

        last_message = darshan.session_history[-1]
        hours_since_last = (datetime.now() - last_message.timestamp).total_seconds() / 3600
        return hours_since_last >= self.SESSION_GAP_HOURS

    def _is_session_transition_from_data(self, session_data: Dict) -> bool:
        """Check session transition from raw data."""
        last_message_at = session_data.get("last_message_at")
        if not last_message_at:
            return False

        if isinstance(last_message_at, str):
            last_message_at = datetime.fromisoformat(last_message_at)

        hours_since_last = (datetime.now() - last_message_at).total_seconds() / 3600
        return hours_since_last >= self.SESSION_GAP_HOURS

    async def distill_session_memory(
        self,
        session_data: Dict,
        child_data: Dict,
    ) -> ConversationMemory:
        """
        Distill session into memory on transition.

        This is called synchronously when session transitions.
        Uses REGULAR model for summarization.
        """
        # For now, create a simple summary
        # Full implementation would use LLM
        history = session_data.get("history", [])
        turn_count = len(history)

        summary = f"Previous session with {turn_count} turns."

        return ConversationMemory.create(
            summary=summary,
            turn_count=turn_count,
        )

    async def persist_darshan(self, family_id: str, darshan: Darshan):
        """Persist child and session state."""
        # Get state for persistence
        darshan_state = darshan.get_state_for_persistence()

        # Build child data
        child_data = {
            "id": family_id,
            "name": darshan.child_name,
            "understanding": {
                "observations": [
                    {
                        "content": f.content,
                        "domain": f.domain,
                        "source": f.source,
                        "confidence": f.confidence,
                    }
                    for f in darshan.understanding.observations
                ],
                "milestones": [
                    {
                        "id": m.id,
                        "description": m.description,
                        "age_months": m.age_months,
                        "age_description": m.age_description,
                        "domain": m.domain,
                        "milestone_type": m.milestone_type,
                        "source": m.source,
                        "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None,
                        "notes": m.notes,
                    }
                    for m in darshan.understanding.milestones
                ],
            },
            "explorations": [
                {
                    "id": c.id,
                    "curiosity_type": c.curiosity_type,
                    "focus": c.focus,
                    "focus_domain": c.focus_domain,
                    "status": c.status,
                    "theory": c.theory,
                    "confidence": c.confidence,
                    "video_appropriate": c.video_appropriate,
                    "question": c.question,
                    # Video consent fields
                    "video_accepted": c.video_accepted,
                    "video_declined": c.video_declined,
                    "video_suggested_at": c.video_suggested_at.isoformat() if c.video_suggested_at else None,
                    # Video scenarios
                    "video_scenarios": [
                        {
                            "id": s.id,
                            "title": s.title,
                            "what_to_film": s.what_to_film,
                            "rationale_for_parent": s.rationale_for_parent,
                            "duration_suggestion": s.duration_suggestion,
                            "example_situations": s.example_situations,
                            "target_hypothesis_id": s.target_hypothesis_id,
                            "what_we_hope_to_learn": s.what_we_hope_to_learn,
                            "focus_points": s.focus_points,
                            "category": s.category,
                            "status": s.status,
                            "created_at": s.created_at.isoformat() if s.created_at else None,
                            "reminder_dismissed": s.reminder_dismissed,
                            "video_path": s.video_path,
                            "uploaded_at": s.uploaded_at.isoformat() if s.uploaded_at else None,
                            "analysis_result": s.analysis_result,
                            "analyzed_at": s.analyzed_at.isoformat() if s.analyzed_at else None,
                        }
                        for s in c.video_scenarios
                    ],
                    # Evidence
                    "evidence": [
                        {
                            "content": e.content,
                            "effect": e.effect,
                            "source": e.source,
                            "timestamp": e.timestamp.isoformat(),
                        }
                        for e in c.evidence
                    ],
                }
                for c in darshan.explorations
            ],
            "stories": [
                {
                    "summary": s.summary,
                    "reveals": s.reveals,
                    "domains": s.domains,
                    "significance": s.significance,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in darshan.stories
            ],
            "journal": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "summary": e.summary,
                    "learned": e.learned,
                    "significance": e.significance,
                    "entry_type": e.entry_type,
                }
                for e in darshan.journal
            ],
            "curiosities": darshan_state["curiosities"],
        }

        # Include crystal if present
        if "crystal" in darshan_state:
            child_data["crystal"] = darshan_state["crystal"]

        # Include shared summaries
        if "shared_summaries" in darshan_state:
            child_data["shared_summaries"] = darshan_state["shared_summaries"]

        # Include session flags (guided collection mode, etc.)
        if "session_flags" in darshan_state:
            child_data["session_flags"] = darshan_state["session_flags"]

        # Include session history for conversation persistence
        if "session_history" in darshan_state:
            child_data["session_history"] = darshan_state["session_history"]

        # Persist to our own file (Darshan's state)
        # SessionService persists sessions automatically
        await self._persist_darshan_to_file(family_id, child_data)

    async def _persist_darshan_to_file(self, family_id: str, darshan_data: Dict[str, Any]):
        """Persist Darshan state to JSON file."""
        # Use a separate directory for gestalt data
        gestalt_dir = Path("data/children")
        gestalt_dir.mkdir(parents=True, exist_ok=True)

        file_path = gestalt_dir / f"{family_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(darshan_data, f, ensure_ascii=False, indent=2, default=str)


# Singleton accessor
_gestalt_manager: Optional[GestaltManager] = None


def get_gestalt_manager(child_service=None, session_service=None) -> GestaltManager:
    """
    Get the GestaltManager instance.

    On first call, must provide services. Subsequent calls return cached instance.
    """
    global _gestalt_manager
    if _gestalt_manager is None:
        if not all([child_service, session_service]):
            raise ValueError("GestaltManager requires services on first initialization")
        _gestalt_manager = GestaltManager(
            child_service=child_service,
            session_service=session_service,
        )
    return _gestalt_manager
