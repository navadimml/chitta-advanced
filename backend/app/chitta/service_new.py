"""
Chitta Service - Thin Orchestration Layer

Orchestrates conversation through the Living Gestalt.

KEY RESPONSIBILITIES:
- Get/create Gestalt for family
- Detect session transitions (>4 hour gap)
- Trigger memory distillation on transition
- Persist state after each message
- Derive action cards

This is a THIN layer - the intelligence lives in the Gestalt.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .gestalt_new import LivingGestalt
from .curiosity import Curiosity
from .models import SynthesisReport, ConversationMemory

# Import existing services for persistence
from app.services.child_service import ChildService
from app.services.session_service import SessionService


logger = logging.getLogger(__name__)


class ChittaServiceNew:
    """
    Orchestrates conversation through the Living Gestalt.

    KEY RESPONSIBILITIES:
    - Get/create Gestalt for family
    - Detect session transitions (>4 hour gap)
    - Trigger memory distillation on transition
    - Persist state after each message
    """

    SESSION_GAP_HOURS = 4  # Hours that define a session transition

    def __init__(
        self,
        child_service: Optional[ChildService] = None,
        session_service: Optional[SessionService] = None,
    ):
        """
        Initialize the service.

        Args:
            child_service: Service for child data persistence
            session_service: Service for session data persistence
        """
        self._child_service = child_service or ChildService()
        self._session_service = session_service or SessionService()
        self._gestalts: Dict[str, LivingGestalt] = {}

    async def process_message(self, family_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process a message through the Gestalt.

        Flow:
        1. Get or create Gestalt
        2. Check for session transition - distill memory if needed
        3. Process message through Gestalt (two-phase)
        4. Persist state
        5. Return response with curiosity state
        """
        # 1. Get gestalt (handles session transition)
        gestalt = await self._get_gestalt_with_transition_check(family_id)

        # 2. Process through Gestalt (two-phase internally)
        response = await gestalt.process_message(user_message)

        # 3. Persist
        await self._persist_gestalt(family_id, gestalt)

        # 4. Return response
        return {
            "response": response.text,
            "curiosity_state": {
                "active_curiosities": [
                    self._curiosity_to_dict(c)
                    for c in response.curiosities[:5]
                ],
                "open_questions": response.open_questions,
            },
            "cards": self._derive_cards(gestalt),
        }

    async def request_synthesis(self, family_id: str) -> Dict[str, Any]:
        """
        User-requested synthesis.

        Uses STRONGEST model for deep analysis.
        """
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        report = gestalt.synthesize()
        if not report:
            return {"error": "Not enough data for synthesis"}

        # Persist any updates
        await self._persist_gestalt(family_id, gestalt)

        return {
            "essence_narrative": report.essence_narrative,
            "patterns": [
                {"description": p.description, "domains": p.domains_involved}
                for p in report.patterns
            ],
            "confidence_by_domain": report.confidence_by_domain,
            "open_questions": report.open_questions,
        }

    async def get_curiosity_state(self, family_id: str) -> Dict[str, Any]:
        """Get current curiosity state for a family."""
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"active_curiosities": [], "open_questions": []}

        curiosities = gestalt.get_active_curiosities()
        return {
            "active_curiosities": [
                self._curiosity_to_dict(c)
                for c in curiosities[:5]
            ],
            "open_questions": gestalt._curiosity_engine.get_gaps(),
        }

    # ========================================
    # GESTALT MANAGEMENT
    # ========================================

    async def _get_gestalt_with_transition_check(self, family_id: str) -> LivingGestalt:
        """
        Get Gestalt, handling session transition if needed.

        Session transition occurs when:
        - Previous session exists AND
        - Gap > 4 hours since last message

        On transition:
        - Distill previous session into memory
        - Start new session with memory context
        """
        # Check cache first
        if family_id in self._gestalts:
            gestalt = self._gestalts[family_id]
            if not self._is_session_transition(gestalt):
                return gestalt

        # Load child data
        child_data = await self._child_service.get_child(family_id)
        if not child_data:
            # Create new child
            child_data = await self._child_service.create_child(family_id)

        # Load session data
        session_data = await self._session_service.get_current_session(family_id)

        # Check for session transition
        if session_data and self._is_session_transition_from_data(session_data):
            # Distill previous session memory
            memory = await self._distill_session_memory(session_data, child_data)

            # Create new session with memory
            session_data = await self._session_service.create_session(
                family_id,
                previous_memory=memory,
            )

        # Create or get session
        if not session_data:
            session_data = await self._session_service.create_session(family_id)

        # Build Gestalt from data
        gestalt = LivingGestalt.from_child_data(
            child_id=family_id,
            child_name=child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            exploration_cycles_data=child_data.get("exploration_cycles"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            curiosity_data=child_data.get("curiosity_engine"),
            session_history_data=session_data.get("history"),
        )

        # Cache it
        self._gestalts[family_id] = gestalt

        return gestalt

    async def _get_gestalt(self, family_id: str) -> Optional[LivingGestalt]:
        """Get Gestalt without transition check."""
        if family_id in self._gestalts:
            return self._gestalts[family_id]

        child_data = await self._child_service.get_child(family_id)
        if not child_data:
            return None

        session_data = await self._session_service.get_current_session(family_id)

        return LivingGestalt.from_child_data(
            child_id=family_id,
            child_name=child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            exploration_cycles_data=child_data.get("exploration_cycles"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            curiosity_data=child_data.get("curiosity_engine"),
            session_history_data=session_data.get("history") if session_data else None,
        )

    def _is_session_transition(self, gestalt: LivingGestalt) -> bool:
        """Check if enough time has passed to consider this a new session."""
        if not gestalt.session_history:
            return False

        last_message = gestalt.session_history[-1]
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

    async def _distill_session_memory(
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

    async def _persist_gestalt(self, family_id: str, gestalt: LivingGestalt):
        """Persist child and session state."""
        # Get state for persistence
        gestalt_state = gestalt.get_state_for_persistence()

        # Build child data
        child_data = {
            "id": family_id,
            "name": gestalt.child_name,
            "understanding": {
                "facts": [
                    {
                        "content": f.content,
                        "domain": f.domain,
                        "source": f.source,
                        "confidence": f.confidence,
                    }
                    for f in gestalt.understanding.facts
                ],
            },
            "exploration_cycles": [
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
                }
                for c in gestalt.exploration_cycles
            ],
            "stories": [
                {
                    "summary": s.summary,
                    "reveals": s.reveals,
                    "domains": s.domains,
                    "significance": s.significance,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in gestalt.stories
            ],
            "journal": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "summary": e.summary,
                    "learned": e.learned,
                    "significance": e.significance,
                }
                for e in gestalt.journal
            ],
            "curiosity_engine": gestalt_state["curiosity_engine"],
        }

        # Build session data
        session_data = {
            "family_id": family_id,
            "history": gestalt_state["session_history"],
            "last_message_at": datetime.now().isoformat(),
        }

        # Persist
        await self._child_service.save_child(family_id, child_data)
        await self._session_service.save_session(family_id, session_data)

    # ========================================
    # CARD DERIVATION
    # ========================================

    def _derive_cards(self, gestalt: LivingGestalt) -> List[Dict]:
        """Derive action cards from current state."""
        cards = []

        # Video suggestion card for video-appropriate hypotheses
        for cycle in gestalt.exploration_cycles:
            if cycle.status == "active" and cycle.video_appropriate:
                cards.append({
                    "type": "video_suggestion",
                    "reason": f"לחקור: {cycle.focus}",
                    "cycle_id": cycle.id,
                })
                break  # One video suggestion at a time

        # Synthesis suggestion when conditions are ripe
        if gestalt._should_synthesize():
            cards.append({
                "type": "synthesis_available",
                "reason": "יש מספיק מידע ליצור סיכום",
            })

        return cards

    # ========================================
    # HELPERS
    # ========================================

    def _curiosity_to_dict(self, curiosity: Curiosity) -> Dict[str, Any]:
        """Convert curiosity to dict for API response."""
        result = {
            "focus": curiosity.focus,
            "type": curiosity.type,
            "activation": curiosity.activation,
            "certainty": curiosity.certainty,
        }

        if curiosity.type == "hypothesis":
            result["theory"] = curiosity.theory
            result["video_appropriate"] = curiosity.video_appropriate

        if curiosity.type == "question":
            result["question"] = curiosity.question

        if curiosity.type == "pattern":
            result["domains_involved"] = curiosity.domains_involved

        return result


# Singleton instance for easy access
_service_instance: Optional[ChittaServiceNew] = None


def get_chitta_service() -> ChittaServiceNew:
    """Get or create the Chitta service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChittaServiceNew()
    return _service_instance
