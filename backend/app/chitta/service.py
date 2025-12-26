"""
Chitta Service - Thin Orchestration Layer

Public API for Chitta. Delegates to specialized services:

- GestaltManager: Darshan lifecycle, session transitions, persistence
- VideoService: Video consent → guidelines → upload → analysis workflow
- ChildSpaceService: Living Portrait derivation (read-only)
- SharingService: Shareable summary generation
- CardsService: Context card derivation
- JournalService: Parent journal entry processing

The intelligence lives in Darshan (gestalt.py).
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .gestalt import Darshan
from .curiosity_types import BaseCuriosity, Discovery, Question, Hypothesis, Pattern
from .models import SynthesisReport, Crystal, ParentContext
from .synthesis import get_synthesis_service
from .child_space import get_child_space_service
from .sharing import get_sharing_service
from .journal_service import get_journal_service
from .cards import get_cards_service
from .video_service import get_video_service
from .gestalt_manager import get_gestalt_manager

# Import existing services for persistence
from app.services.child_service import ChildService
from app.services.session_service import SessionService


logger = logging.getLogger(__name__)


class ChittaService:
    """
    Thin orchestration layer - delegates to specialized services.

    This is the PUBLIC API for Chitta. All intelligence lives in:
    - Darshan (gestalt.py) - the observing intelligence
    - GestaltManager - Darshan lifecycle & persistence
    - VideoService - video consent → guidelines → upload → analysis
    - ChildSpaceService - Living Portrait derivation
    - SharingService - shareable summary generation
    - CardsService - context card derivation
    - JournalService - parent journal processing
    """

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
        self._gestalt_manager = get_gestalt_manager(
            child_service=self._child_service,
            session_service=self._session_service,
        )
        self._child_space_service = get_child_space_service()
        self._sharing_service = get_sharing_service()
        self._journal_service = get_journal_service()
        self._cards_service = get_cards_service()
        self._video_service = get_video_service(
            get_darshan=self._gestalt_manager.get_darshan,
            persist_darshan=self._gestalt_manager.persist_darshan,
            get_cards_callback=self._cards_service.derive_cards,
        )

    async def process_message(
        self,
        family_id: str,
        user_message: str,
        parent_context: Optional[ParentContext] = None,
    ) -> Dict[str, Any]:
        """
        Process a message through the Gestalt.

        Flow:
        1. Get or create Gestalt
        2. Check for session transition - distill memory if needed
        3. Process message through Gestalt (two-phase)
        4. Persist state
        5. Trigger background crystallization if important moment
        6. Return response with curiosity state

        Args:
            family_id: The child/family ID
            user_message: The message from the parent
            parent_context: Parent context for gender-appropriate responses
        """
        # 1. Get gestalt (handles session transition)
        gestalt = await self._gestalt_manager.get_darshan_with_transition_check(family_id)

        # Set parent context for gender-appropriate responses
        if parent_context:
            gestalt.parent_context = parent_context

        # 2. Process through Gestalt (two-phase internally)
        response = await gestalt.process_message(user_message)

        # 3. Persist
        await self._gestalt_manager.persist_darshan(family_id, gestalt)

        # 4. Background crystallization if important moment occurred
        if response.should_crystallize:
            # Fire-and-forget crystallization to not block response
            import asyncio
            asyncio.create_task(self._background_crystallize(family_id))
            logger.info(f"Triggered background crystallization for {family_id}")

        # 5. Return response
        return {
            "response": response.text,
            "curiosity_state": {
                "active_curiosities": [
                    self._curiosity_to_dict(c)
                    for c in response.curiosities[:5]
                ],
                "open_questions": response.open_questions,
            },
            "cards": self._cards_service.derive_cards(gestalt),
        }

    async def _background_crystallize(self, family_id: str):
        """
        Background crystallization - doesn't block the response.

        Called when an important moment occurs (story captured, hypothesis formed, etc.)
        Updates the Crystal so future responses have holistic context.
        """
        try:
            await self.crystallize(family_id)
            logger.info(f"Background crystallization completed for {family_id}")
        except Exception as e:
            logger.error(f"Background crystallization failed for {family_id}: {e}")

    async def request_synthesis(self, family_id: str) -> Dict[str, Any]:
        """
        User-requested synthesis.

        Uses STRONGEST model for deep analysis.
        """
        gestalt = await self._gestalt_manager.get_darshan(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        report = gestalt.synthesize()
        if not report:
            return {"error": "Not enough data for synthesis"}

        # Persist any updates
        await self._gestalt_manager.persist_darshan(family_id, gestalt)

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
        gestalt = await self._gestalt_manager.get_darshan(family_id)
        if not gestalt:
            return {"active_curiosities": [], "open_questions": [], "suggest_baseline_video": False}

        curiosities = gestalt.get_active_curiosities()

        # Check if we should suggest baseline video
        # Early in conversation (5-15 messages) when seeing the child would help
        message_count = len(gestalt.session_history)
        video_hypotheses = gestalt._curiosity_manager.get_video_appropriate_hypotheses()
        suggest_baseline_video = (
            5 <= message_count <= 15 and
            len(video_hypotheses) == 0  # No video-appropriate hypotheses yet
        )

        return {
            "active_curiosities": [
                self._curiosity_to_dict(c)
                for c in curiosities[:5]
            ],
            "open_questions": [c.focus for c in gestalt._curiosity_manager.get_gaps()],
            "suggest_baseline_video": suggest_baseline_video,
        }

    async def get_cards(self, family_id: str) -> List[Dict]:
        """
        Get current context cards for a family.

        Delegates to CardsService for the actual derivation.
        """
        darshan = await self._gestalt_manager.get_darshan(family_id)
        if not darshan:
            return []

        return self._cards_service.derive_cards(darshan)

    async def get_gestalt(self, family_id: str) -> Optional[Darshan]:
        """
        Get Darshan (gestalt) for a family.

        Public API for routes that need direct gestalt access.
        """
        return await self._gestalt_manager.get_darshan(family_id)

    async def get_child_space(self, family_id: str) -> Dict[str, Any]:
        """
        Get child space data for the Living Portrait UI.

        Returns header data (child_name, badges) for the ChildSpaceHeader component.
        """
        darshan = await self._gestalt_manager.get_darshan(family_id)
        if not darshan:
            return {"child_name": None, "badges": []}

        return self._child_space_service.derive_child_space_header(darshan)

    # ========================================
    # CRYSTALLIZATION
    # ========================================

    async def crystallize(self, family_id: str, force: bool = False) -> Crystal:
        """
        Trigger crystallization for a family's gestalt.

        Creates or updates the Crystal (cached synthesis) based on current observations.
        Uses incremental update if previous crystal exists.

        Args:
            family_id: The family ID
            force: If True, create fresh crystal even if existing one is not stale

        Returns:
            Crystal: The new or updated crystal
        """
        gestalt = await self._gestalt_manager.get_darshan(family_id)
        if not gestalt:
            raise ValueError(f"No gestalt found for family_id: {family_id}")

        # Check if crystallization is needed
        if not force and gestalt.crystal and not gestalt.is_crystal_stale():
            logger.info(f"Crystal for {family_id} is fresh, skipping crystallization")
            return gestalt.crystal

        synthesis_service = get_synthesis_service()
        latest_observation_at = gestalt.get_latest_observation_timestamp()

        # Get existing pattern descriptions to detect new ones
        existing_pattern_descriptions = set()
        if gestalt.crystal and gestalt.crystal.patterns:
            existing_pattern_descriptions = {p.description for p in gestalt.crystal.patterns}

        crystal = await synthesis_service.crystallize(
            child_name=gestalt.child_name,
            understanding=gestalt.understanding,
            stories=gestalt.stories,
            curiosities=gestalt._curiosities,
            latest_observation_at=latest_observation_at,
            existing_crystal=gestalt.crystal,
        )

        # Add journal entries for NEW patterns found
        if crystal.patterns:
            for pattern in crystal.patterns:
                if pattern.description not in existing_pattern_descriptions:
                    from .models import JournalEntry
                    gestalt.journal.append(JournalEntry.create(
                        summary=pattern.description,
                        learned=[f"תחומים: {', '.join(pattern.domains_involved)}"] if pattern.domains_involved else [],
                        significance="notable",
                        entry_type="pattern_found",
                    ))
                    logger.info(f"🔮 New pattern journaled: {pattern.description[:50]}...")

        # Update gestalt with new crystal
        gestalt.crystal = crystal

        # Persist
        await self._gestalt_manager.persist_darshan(family_id, gestalt)

        logger.info(f"Crystallized gestalt for {family_id}, version {crystal.version}")
        return crystal

    async def ensure_crystal_fresh(self, family_id: str) -> Crystal:
        """
        Ensure the crystal is fresh before returning child space data.

        If crystal is stale or missing, triggers crystallization.
        If crystal is fresh, returns it directly.

        This is the method to call when ChildSpace is opened.
        """
        gestalt = await self._gestalt_manager.get_darshan(family_id)
        if not gestalt:
            raise ValueError(f"No gestalt found for family_id: {family_id}")

        # If no observations yet, return empty crystal
        if not gestalt.understanding.observations and not gestalt.stories:
            return Crystal.create_empty()

        # If crystal is fresh, return it
        if gestalt.crystal and not gestalt.is_crystal_stale():
            return gestalt.crystal

        # Otherwise, crystallize
        return await self.crystallize(family_id)

    # ========================================
    # VIDEO WORKFLOW - DELEGATED TO video_service.py
    # ========================================

    async def accept_video_suggestion(
        self, family_id: str, cycle_id: str, generate_async: bool = True
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.accept_video_suggestion(family_id, cycle_id, generate_async)

    async def decline_video_suggestion(self, family_id: str, cycle_id: str) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.decline_video_suggestion(family_id, cycle_id)

    async def accept_baseline_video(
        self, family_id: str, generate_async: bool = True
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.accept_baseline_video(family_id, generate_async)

    async def dismiss_baseline_video(self, family_id: str) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.dismiss_baseline_video(family_id)

    async def get_video_guidelines(self, family_id: str, cycle_id: str) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.get_video_guidelines(family_id, cycle_id)

    async def dismiss_scenario_reminders(
        self, family_id: str, scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.dismiss_scenario_reminders(family_id, scenario_ids)

    async def reject_scenarios(
        self, family_id: str, scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.reject_scenarios(family_id, scenario_ids)

    async def acknowledge_video_insights(
        self, family_id: str, scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.acknowledge_video_insights(family_id, scenario_ids)

    async def confirm_video(
        self, family_id: str, scenario_id: str
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.confirm_video(family_id, scenario_id)

    async def reject_confirmed_video(
        self, family_id: str, scenario_id: str
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.reject_confirmed_video(family_id, scenario_id)

    async def record_video_upload(
        self,
        family_id: str,
        scenario_id: str,
        file_path: str,
        duration_seconds: int = 0
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.record_video_upload(family_id, scenario_id, file_path, duration_seconds)

    async def mark_video_uploaded(
        self,
        family_id: str,
        cycle_id: str,
        scenario_id: str,
        video_path: str,
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.mark_video_uploaded(family_id, cycle_id, scenario_id, video_path)

    async def analyze_cycle_videos(
        self, family_id: str, cycle_id: str
    ) -> Dict[str, Any]:
        """Delegate to VideoService."""
        return await self._video_service.analyze_cycle_videos(family_id, cycle_id)

    # ========================================
    # RETURNING USER CHECK
    # ========================================

    def _check_returning_user(self, session: Any, child: Any) -> Optional[Dict[str, Any]]:
        """
        Check if this is a returning user and return context about their absence.

        Returns None for new users, or a dict with:
        - category: "returning" | "long_absence"
        - days_since: number of days since last activity
        """
        if not session or not hasattr(session, 'last_activity_at'):
            return None

        last_activity = session.last_activity_at
        if not last_activity:
            return None

        # Calculate days since last activity
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            except ValueError:
                return None

        now = datetime.now(last_activity.tzinfo) if last_activity.tzinfo else datetime.now()
        days_since = (now - last_activity).days

        # Only show returning context if at least 1 day has passed
        if days_since < 1:
            return None

        category = "long_absence" if days_since >= 14 else "returning"
        return {
            "category": category,
            "days_since": days_since,
        }

    # ========================================
    # HELPERS
    # ========================================

    def _curiosity_to_dict(self, curiosity: BaseCuriosity) -> Dict[str, Any]:
        """Convert curiosity to dict for API response."""
        # Determine type from class
        if isinstance(curiosity, Hypothesis):
            curiosity_type = "hypothesis"
            certainty = curiosity.confidence
        elif isinstance(curiosity, Question):
            curiosity_type = "question"
            certainty = curiosity.fullness
        elif isinstance(curiosity, Pattern):
            curiosity_type = "pattern"
            certainty = curiosity.confidence
        elif isinstance(curiosity, Discovery):
            curiosity_type = "discovery"
            certainty = curiosity.fullness
        else:
            curiosity_type = "discovery"
            certainty = 0.5

        result = {
            "focus": curiosity.focus,
            "type": curiosity_type,
            "pull": curiosity.pull,
            "certainty": certainty,
        }

        if isinstance(curiosity, Hypothesis):
            result["theory"] = curiosity.theory
            result["video_appropriate"] = curiosity.video_appropriate

        if isinstance(curiosity, Question):
            result["question"] = curiosity.question

        if isinstance(curiosity, Pattern):
            result["domains_involved"] = curiosity.domains_involved

        return result

    # ========================================
    # CHILD SPACE - DELEGATED TO child_space.py
    # ========================================

    def derive_child_space_full(self, gestalt: Darshan) -> Dict[str, Any]:
        """Delegate to ChildSpaceService for Living Portrait UI data."""
        return self._child_space_service.derive_child_space_full(gestalt)

    def derive_child_space_header(self, gestalt: Darshan) -> Dict[str, Any]:
        """Delegate to ChildSpaceService for header data."""
        return self._child_space_service.derive_child_space_header(gestalt)

    async def generate_shareable_summary(
        self,
        family_id: str,
        expert: Optional[Dict[str, Any]] = None,
        expert_description: Optional[str] = None,
        crystal_insights: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None,
        comprehensive: bool = False,
        missing_gaps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a shareable summary using STRUCTURED OUTPUT.

        Delegates to SharingService for the actual generation.
        """
        darshan = await self._gestalt_manager.get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found", "content": ""}

        # Create persist callback for the sharing service
        async def persist_callback(d: Darshan) -> None:
            await self._gestalt_manager.persist_darshan(family_id, d)

        return await self._sharing_service.generate_shareable_summary(
            darshan=darshan,
            persist_callback=persist_callback,
            expert=expert,
            expert_description=expert_description,
            crystal_insights=crystal_insights,
            additional_context=additional_context,
            comprehensive=comprehensive,
            missing_gaps=missing_gaps,
        )

    # =========================================================================
    # PARENT JOURNAL INTEGRATION - DELEGATED TO journal_service.py
    # =========================================================================

    async def process_parent_journal_entry(
        self,
        family_id: str,
        entry_text: str,
        entry_type: str,  # "התקדמות" | "תצפית" | "אתגר"
    ) -> Dict[str, Any]:
        """
        Process a parent journal entry and feed it into understanding.

        Delegates to JournalService for the actual processing.
        """
        darshan = await self._load_gestalt(family_id)

        # Create persist callback for the journal service
        async def persist_callback(d: Darshan) -> None:
            await self._gestalt_manager.persist_darshan(family_id, d)

        return await self._journal_service.process_parent_journal_entry(
            darshan=darshan,
            entry_text=entry_text,
            entry_type=entry_type,
            persist_callback=persist_callback,
            get_llm_callback=self._get_llm,
        )


# Singleton instance for easy access
_service_instance: Optional[ChittaService] = None


def get_chitta_service() -> ChittaService:
    """Get or create the Chitta service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChittaService()
    return _service_instance
