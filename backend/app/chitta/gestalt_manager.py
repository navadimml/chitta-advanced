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
            curiosity_manager_data=child_data.get("curiosity_manager"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
            shared_summaries_data=child_data.get("shared_summaries"),
            child_birth_date=child_birth_date,
            session_flags_data=child_data.get("session_flags"),
            child_gender=child_gender,
            session_id=child_data.get("session_id"),
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
            curiosity_manager_data=child_data.get("curiosity_manager"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
            shared_summaries_data=child_data.get("shared_summaries"),
            child_birth_date=child_birth_date,
            session_flags_data=child_data.get("session_flags"),
            child_gender=child_gender,
            session_id=child_data.get("session_id"),
        )

        # Cache it
        self._gestalts[family_id] = darshan
        return darshan

    async def _load_darshan_data_from_db(self, family_id: str) -> Dict[str, Any]:
        """Load Darshan data from database."""
        try:
            async with UnitOfWork() as uow:
                data = await uow.darshan.load_darshan_data(family_id)
                if data and (data.get("curiosity_manager") or data.get("journal") or data.get("crystal")):
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
            "curiosity_manager": None,
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
            "curiosity_manager": darshan_state.get("curiosity_manager", {}),
            "session_id": darshan_state.get("session_id"),
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

        # Add child identity (name, gender, birth_date)
        if darshan_state.get("name"):
            darshan_data["name"] = darshan_state["name"]
        if darshan_state.get("child_gender"):
            darshan_data["child_gender"] = darshan_state["child_gender"]
        if darshan_state.get("child_birth_date"):
            darshan_data["child_birth_date"] = darshan_state["child_birth_date"]

        # Add understanding (observations, patterns, milestones)
        if darshan_state.get("understanding"):
            darshan_data["understanding"] = darshan_state["understanding"]

        # Add crystal if present
        if darshan_state.get("crystal"):
            darshan_data["crystal"] = darshan_state["crystal"]

        # Save to database
        try:
            async with UnitOfWork() as uow:
                await uow.darshan.save_darshan_data(family_id, darshan_data)

                # Persist cognitive turns for dashboard (separate table)
                latest_turn = darshan.get_latest_cognitive_turn()
                if latest_turn:
                    await self._persist_cognitive_turn(uow, latest_turn)

                await uow.commit()
                logger.info(f"Persisted darshan data for {family_id} to database")
        except Exception as e:
            logger.error(f"Failed to persist darshan data to DB for {family_id}: {e}")
            raise

    async def _persist_cognitive_turn(self, uow: UnitOfWork, turn):
        """
        Persist a cognitive turn to the database for dashboard review.

        Cognitive turns are stored separately from the main Darshan state
        to support the expert review dashboard.
        """
        from .models import CognitiveTurn as CognitiveTurnModel

        # Check if this turn already exists (idempotency)
        existing = await uow.dashboard.cognitive_turns.get_by_turn_id(turn.turn_id)
        if existing:
            logger.debug(f"Cognitive turn {turn.turn_id} already persisted, skipping")
            return

        # Convert tool calls to serializable format
        tool_calls_data = None
        if turn.tool_calls:
            tool_calls_data = [
                {"tool_name": tc.tool_name, "arguments": tc.arguments}
                for tc in turn.tool_calls
            ]

        # Convert state delta to serializable format
        state_delta_data = None
        if turn.state_delta:
            state_delta_data = {
                "observations_added": turn.state_delta.observations_added,
                "curiosities_spawned": turn.state_delta.curiosities_spawned,
                "evidence_added": turn.state_delta.evidence_added,
                "child_identity_set": turn.state_delta.child_identity_set,
            }

        # Create the database record
        await uow.dashboard.cognitive_turns.create_turn(
            turn_id=turn.turn_id,
            turn_number=turn.turn_number,
            child_id=turn.child_id,
            timestamp=turn.timestamp,
            parent_message=turn.parent_message,
            parent_role=turn.parent_role,
            tool_calls=tool_calls_data,
            perceived_intent=turn.perceived_intent,
            state_delta=state_delta_data,
            turn_guidance=turn.turn_guidance,
            active_curiosities=turn.active_curiosities,
            response_text=turn.response_text,
        )
        logger.info(f"Persisted cognitive turn {turn.turn_id} for dashboard")


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
