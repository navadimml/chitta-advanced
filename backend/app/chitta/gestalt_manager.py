"""
Gestalt Manager - Darshan Lifecycle & Persistence

Manages the lifecycle of Darshan instances:
- Loading from persistence (database)
- Detecting session transitions (>4 hour gaps)
- Memory distillation on session transitions
- Persisting state to database

Philosophy:
- Darshan is the observing intelligence
- State is preserved across sessions
- Memory is distilled when sessions transition
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .gestalt import Darshan
from .models import ConversationMemory
from app.db.repositories import UnitOfWork

logger = logging.getLogger(__name__)


class GestaltManager:
    """
    Manages Darshan lifecycle: loading, caching, transition detection, persistence.

    Uses database for persistence via UnitOfWork.
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

        # Build Darshan from persisted data (database)
        child_data = await self._load_darshan_data_from_db(family_id)

        # Session history from child_data
        session_history = child_data.get("session_history", [])

        # Get child's birth date for temporal calculations
        child_birth_date = None
        if hasattr(child, 'identity') and child.identity and child.identity.birth_date:
            child_birth_date = child.identity.birth_date

        # Get child's gender from identity or data
        child_gender = None
        if hasattr(child, 'identity') and child.identity and hasattr(child.identity, 'gender'):
            child_gender = child.identity.gender
        if not child_gender:
            child_gender = child_data.get("child_gender")

        darshan = Darshan.from_child_data(
            child_id=family_id,
            child_name=child.name or child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            curiosities_data=child_data.get("curiosity_engine") or child_data.get("curiosities"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
            shared_summaries_data=child_data.get("shared_summaries"),
            child_birth_date=child_birth_date,
            session_flags_data=child_data.get("session_flags"),
            child_gender=child_gender,
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

        # Extract data from database
        child_data = await self._load_darshan_data_from_db(family_id)

        # Session history from child_data
        session_history = child_data.get("session_history", [])

        # Get child's birth date for temporal calculations
        child_birth_date = None
        if hasattr(child, 'identity') and child.identity and child.identity.birth_date:
            child_birth_date = child.identity.birth_date

        # Get child's gender from identity or data
        child_gender = None
        if hasattr(child, 'identity') and child.identity and hasattr(child.identity, 'gender'):
            child_gender = child.identity.gender
        if not child_gender:
            child_gender = child_data.get("child_gender")

        darshan = Darshan.from_child_data(
            child_id=family_id,
            child_name=child.name or child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            curiosities_data=child_data.get("curiosity_engine") or child_data.get("curiosities"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
            shared_summaries_data=child_data.get("shared_summaries"),
            child_birth_date=child_birth_date,
            session_flags_data=child_data.get("session_flags"),
            child_gender=child_gender,
        )

        # Cache it
        self._gestalts[family_id] = darshan
        return darshan

    async def _load_darshan_data_from_db(self, family_id: str) -> Dict[str, Any]:
        """Load Darshan data from database."""
        try:
            async with UnitOfWork() as uow:
                data = await uow.darshan.load_darshan_data(family_id)
                if data and (data.get("curiosities") or data.get("journal") or data.get("crystal")):
                    logger.info(f"Loaded darshan data for {family_id} from database")
                    return data
        except Exception as e:
            logger.warning(f"Failed to load darshan data from DB for {family_id}: {e}")

        # Return empty state - will be built through conversation
        return self._empty_darshan_data()

    def _empty_darshan_data(self) -> Dict[str, Any]:
        """Return empty Darshan state for new conversations."""
        return {
            "understanding": None,
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
        """Persist Darshan state to database."""
        # Get state for persistence
        darshan_state = darshan.get_state_for_persistence()

        # Build the data structure for the repository
        darshan_data = {
            "curiosities": darshan_state.get("curiosities", {}),
            "journal": [
                {
                    "summary": e.summary,
                    "learned": e.learned,
                    "significance": e.significance,
                    "entry_type": e.entry_type,
                    "timestamp": e.timestamp,
                }
                for e in darshan.journal
            ],
            "session_history": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                }
                for m in darshan.session_history
            ],
            "session_flags": darshan_state.get("session_flags", {}),
            "shared_summaries": darshan_state.get("shared_summaries", {}),
        }

        # Add crystal if present
        if darshan_state.get("crystal"):
            darshan_data["crystal"] = darshan_state["crystal"]

        # Save to database
        try:
            async with UnitOfWork() as uow:
                await uow.darshan.save_darshan_data(family_id, darshan_data)
                await uow.commit()
                logger.info(f"Persisted darshan data for {family_id} to database")
        except Exception as e:
            logger.error(f"Failed to persist darshan data to DB for {family_id}: {e}")
            raise


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
