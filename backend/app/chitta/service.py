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

from .gestalt import LivingGestalt
from .curiosity import Curiosity
from .models import SynthesisReport, ConversationMemory, Crystal
from .synthesis import get_synthesis_service

# Import existing services for persistence
from app.services.child_service import ChildService
from app.services.session_service import SessionService


logger = logging.getLogger(__name__)


class ChittaService:
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
        5. Trigger background crystallization if important moment
        6. Return response with curiosity state
        """
        # 1. Get gestalt (handles session transition)
        gestalt = await self._get_gestalt_with_transition_check(family_id)

        # 2. Process through Gestalt (two-phase internally)
        response = await gestalt.process_message(user_message)

        # 3. Persist
        await self._persist_gestalt(family_id, gestalt)

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
            "cards": self._derive_cards(gestalt),
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

        # Load child (returns Child object or creates new one)
        child = await self._child_service.get_or_create_child_async(family_id)

        # Get or create session (using SessionService properly)
        session = await self._session_service.get_or_create_session_async(family_id)

        # Build Gestalt from persisted data
        # Extract data from our own persistence (gestalt files)
        child_data = self._extract_child_data_for_gestalt(child, family_id)

        # Session history from SessionState
        session_history = []
        if session and hasattr(session, 'history'):
            session_history = [
                {"role": m.role, "content": m.content}
                for m in session.history
            ] if session.history else []

        gestalt = LivingGestalt.from_child_data(
            child_id=family_id,
            child_name=child.name or child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            exploration_cycles_data=child_data.get("exploration_cycles"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            curiosity_data=child_data.get("curiosity_engine"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
        )

        # Cache it
        self._gestalts[family_id] = gestalt

        return gestalt

    async def _get_gestalt(self, family_id: str) -> Optional[LivingGestalt]:
        """Get Gestalt without transition check."""
        if family_id in self._gestalts:
            return self._gestalts[family_id]

        # Try to load child - returns Child object
        child = await self._child_service.get_or_create_child_async(family_id)

        # Get or create session
        session = await self._session_service.get_or_create_session_async(family_id)

        # Extract data from our persistence
        child_data = self._extract_child_data_for_gestalt(child, family_id)

        # Session history
        session_history = []
        if session and hasattr(session, 'history'):
            session_history = [
                {"role": m.role, "content": m.content}
                for m in session.history
            ] if session.history else []

        gestalt = LivingGestalt.from_child_data(
            child_id=family_id,
            child_name=child.name or child_data.get("name"),
            understanding_data=child_data.get("understanding"),
            exploration_cycles_data=child_data.get("exploration_cycles"),
            stories_data=child_data.get("stories"),
            journal_data=child_data.get("journal"),
            curiosity_data=child_data.get("curiosity_engine"),
            session_history_data=session_history,
            crystal_data=child_data.get("crystal"),
        )

        # Cache it
        self._gestalts[family_id] = gestalt
        return gestalt

    def _extract_child_data_for_gestalt(self, child, family_id: str = None) -> Dict[str, Any]:
        """Extract data from Child model or file in format expected by LivingGestalt.

        Args:
            child: Child model (may be empty if gestalt file format differs)
            family_id: The family_id to use for file lookup (fallback if child.id fails)
        """
        import json
        from pathlib import Path

        # Try to load from gestalt file using child.id first, then family_id as fallback
        # This handles seeded gestalt data which doesn't have child_id field
        file_id = getattr(child, 'id', None) or family_id
        if not file_id:
            logger.warning("No file_id available for gestalt loading")
            return self._empty_gestalt_data()

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
        return self._empty_gestalt_data()

    def _empty_gestalt_data(self) -> Dict[str, Any]:
        """Return empty gestalt state for new conversations."""
        return {
            "understanding": None,
            "exploration_cycles": [],
            "stories": [],
            "journal": [],
            "curiosity_engine": None,
        }

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

        # Include crystal if present
        if "crystal" in gestalt_state:
            child_data["crystal"] = gestalt_state["crystal"]

        # Persist to our own file (Gestalt's state)
        # SessionService persists sessions automatically
        await self._persist_gestalt_to_file(family_id, child_data)

    async def _persist_gestalt_to_file(self, family_id: str, gestalt_data: Dict[str, Any]):
        """Persist Gestalt state to JSON file."""
        import json
        from pathlib import Path

        # Use a separate directory for gestalt data
        gestalt_dir = Path("data/children")
        gestalt_dir.mkdir(parents=True, exist_ok=True)

        file_path = gestalt_dir / f"{family_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(gestalt_data, f, ensure_ascii=False, indent=2, default=str)

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
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            raise ValueError(f"No gestalt found for family_id: {family_id}")

        # Check if crystallization is needed
        if not force and gestalt.crystal and not gestalt.is_crystal_stale():
            logger.info(f"Crystal for {family_id} is fresh, skipping crystallization")
            return gestalt.crystal

        synthesis_service = get_synthesis_service()
        latest_observation_at = gestalt.get_latest_observation_timestamp()

        crystal = await synthesis_service.crystallize(
            child_name=gestalt.child_name,
            understanding=gestalt.understanding,
            exploration_cycles=gestalt.exploration_cycles,
            stories=gestalt.stories,
            curiosity_engine=gestalt._curiosity_engine,
            latest_observation_at=latest_observation_at,
            existing_crystal=gestalt.crystal,
        )

        # Update gestalt with new crystal
        gestalt.crystal = crystal

        # Persist
        await self._persist_gestalt(family_id, gestalt)

        logger.info(f"Crystallized gestalt for {family_id}, version {crystal.version}")
        return crystal

    async def ensure_crystal_fresh(self, family_id: str) -> Crystal:
        """
        Ensure the crystal is fresh before returning child space data.

        If crystal is stale or missing, triggers crystallization.
        If crystal is fresh, returns it directly.

        This is the method to call when ChildSpace is opened.
        """
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            raise ValueError(f"No gestalt found for family_id: {family_id}")

        # If no observations yet, return empty crystal
        if not gestalt.understanding.facts and not gestalt.stories:
            return Crystal.create_empty()

        # If crystal is fresh, return it
        if gestalt.crystal and not gestalt.is_crystal_stale():
            return gestalt.crystal

        # Otherwise, crystallize
        return await self.crystallize(family_id)

    # ========================================
    # CARD DERIVATION
    # ========================================

    def _derive_cards(self, gestalt: LivingGestalt) -> List[Dict]:
        """
        Derive action cards from current state.

        Video cards follow CONSENT-FIRST approach:
        1. video_suggestion - Ask parent if they want guidelines (NO generation yet)
        2. video_guidelines_ready - After consent, guidelines generated
        3. video_uploaded - Video uploaded, ready for analysis
        4. video_insights - Analysis complete, insights available
        """
        cards = []

        for cycle in gestalt.exploration_cycles:
            if cycle.status != "active":
                continue

            # === VIDEO CARDS (consent-first) ===

            # Stage 1: Suggest video (parent hasn't decided yet)
            # Guidelines NOT generated - only after consent
            if cycle.can_suggest_video() and (cycle.confidence or 0.5) < 0.7:
                cards.append({
                    "type": "video_suggestion",
                    "title": "אפשר להבין את זה טוב יותר בסרטון",
                    "description": "רוצה שאכין לך הנחיות צילום מותאמות?",
                    "dismissible": True,
                    "actions": [
                        {"label": "כן, בבקשה", "action": "accept_video", "primary": True},
                        {"label": "לא עכשיו", "action": "decline_video"}
                    ],
                    "cycle_id": cycle.id,
                    "priority": "medium",
                })
                break  # One suggestion at a time

            # Stage 1.5: Guidelines generating (parent accepted, waiting for LLM)
            if (cycle.video_accepted and
                cycle.guidelines_status == "generating" and
                not cycle.video_scenarios):
                cards.append({
                    "type": "video_guidelines_generating",
                    "title": "מכין הנחיות צילום...",
                    "description": "רק עוד רגע, מכין הנחיות מותאמות אישית",
                    "dismissible": False,
                    "loading": True,
                    "cycle_id": cycle.id,
                    "priority": "high",
                })
                break

            # Stage 2: Check for validation failures FIRST (takes priority)
            failed_scenarios = [s for s in cycle.video_scenarios if s.status == "validation_failed"]
            if failed_scenarios:
                # Get the first failed scenario's validation message
                failed = failed_scenarios[0]
                validation_result = failed.analysis_result.get("video_validation", {}) if failed.analysis_result else {}
                what_video_shows = validation_result.get("what_video_shows", "")
                cards.append({
                    "type": "video_validation_failed",
                    "title": "הסרטון לא תואם לבקשה",
                    "description": what_video_shows if what_video_shows else "נא להעלות סרטון שמתאים להנחיות",
                    "dismissible": True,
                    "actions": [
                        {"label": "ראה הנחיות", "action": "view_guidelines", "primary": True},
                        {"label": "העלה סרטון חדש", "action": "upload_video"}
                    ],
                    "cycle_id": cycle.id,
                    "scenario_id": failed.id,
                    "validation_issues": validation_result.get("validation_issues", []),
                    "priority": "high",
                })
                break

            # Stage 2.5: Guidelines ready (parent accepted, guidelines generated, no uploads yet)
            if (cycle.video_accepted and
                cycle.video_scenarios and
                not cycle.has_pending_videos() and
                not cycle.has_analyzed_videos()):
                cards.append({
                    "type": "video_guidelines_ready",
                    "title": "הנחיות צילום מוכנות",
                    "description": f"{len(cycle.video_scenarios)} תרחישים מותאמים אישית",
                    "dismissible": True,
                    "actions": [
                        {"label": "צפה בהנחיות", "action": "view_guidelines", "primary": True}
                    ],
                    "cycle_id": cycle.id,
                    "priority": "high",
                })
                break

            # Stage 3: Video uploaded, waiting for analysis
            if cycle.has_pending_videos():
                pending_count = sum(1 for s in cycle.video_scenarios if s.status == "uploaded")
                cards.append({
                    "type": "video_uploaded",
                    "title": "סרטון מוכן לצפייה",
                    "description": f"{pending_count} סרטונים מחכים לניתוח",
                    "dismissible": False,
                    "actions": [
                        {"label": "נתח את הסרטונים", "action": "analyze_videos", "primary": True}
                    ],
                    "cycle_id": cycle.id,
                    "priority": "high",
                })
                break

            # Stage 4: Video analyzed, insights available
            analyzed_scenarios = [s for s in cycle.video_scenarios if s.status == "analyzed"]
            if analyzed_scenarios:
                cards.append({
                    "type": "video_insights",
                    "title": "יש תובנות מהסרטון!",
                    "description": "ראיתי את הסרטון ויש לי כמה תובנות לשתף",
                    "dismissible": True,
                    "actions": [
                        {"label": "ראה תובנות", "action": "view_insights", "primary": True}
                    ],
                    "cycle_id": cycle.id,
                    "scenario_ids": [s.id for s in analyzed_scenarios],
                    "priority": "high",
                })
                break

        # Synthesis suggestion when conditions are ripe
        if gestalt._should_synthesize():
            cards.append({
                "type": "synthesis_available",
                "title": "סיכום מוכן",
                "description": "יש מספיק מידע ליצור סיכום",
                "dismissible": True,
                "actions": [
                    {"label": "צפה בסיכום", "action": "view_synthesis", "primary": True}
                ],
                "priority": "low",
            })

        return cards

    def _derive_child_space(self, gestalt: LivingGestalt) -> Dict[str, Any]:
        """
        Derive child space data from gestalt for header badges.

        Returns data for ChildSpaceHeader component:
        - badges: Quick-access pills showing what's available
        - videos: Count of videos with analysis status
        - exploration_summary: Brief summary of active explorations
        """
        badges = []

        # Count videos from exploration cycles
        total_videos = 0
        analyzed_videos = 0
        pending_videos = 0

        for cycle in gestalt.exploration_cycles:
            for scenario in cycle.video_scenarios:
                total_videos += 1
                if scenario.status == "analyzed":
                    analyzed_videos += 1
                elif scenario.status == "uploaded":
                    pending_videos += 1

        # Video badge
        if total_videos > 0:
            if pending_videos > 0:
                badges.append({
                    "slot_id": "videos",
                    "icon": "🎬",
                    "text": f"{pending_videos} ממתין",
                    "status": "pending",
                })
            elif analyzed_videos > 0:
                badges.append({
                    "slot_id": "videos",
                    "icon": "🎬",
                    "text": str(total_videos),
                    "status": "ready",
                })

        # Guidelines badge - check if any cycle has guidelines ready
        has_guidelines = any(
            c.guidelines_status == "ready" and c.video_scenarios
            for c in gestalt.exploration_cycles
        )
        if has_guidelines:
            badges.append({
                "slot_id": "filming_guidelines",
                "icon": "📹",
                "text": "הנחיות",
                "status": "ready",
            })

        # Journal badge - from gestalt.journal
        journal_count = len(gestalt.journal)
        if journal_count > 0:
            badges.append({
                "slot_id": "journal",
                "icon": "📝",
                "text": str(journal_count),
                "status": "ready",
            })

        # Insights badge - if any video has been analyzed
        if analyzed_videos > 0:
            badges.append({
                "slot_id": "insights",
                "icon": "✨",
                "text": "תובנות",
                "status": "ready",
            })

        return {
            "child_name": gestalt.child_name,
            "badges": badges,
            "video_count": total_videos,
            "analyzed_count": analyzed_videos,
            "pending_count": pending_videos,
            "journal_count": journal_count,
            "exploration_count": len([c for c in gestalt.exploration_cycles if c.status == "active"]),
        }

    # ========================================
    # VIDEO CONSENT & GUIDELINES
    # ========================================

    async def accept_video_suggestion(
        self,
        family_id: str,
        cycle_id: str,
        generate_async: bool = True
    ) -> Dict[str, Any]:
        """
        Parent accepted video suggestion.

        Two modes:
        - generate_async=True (default): Mark accepted, return immediately,
          generate guidelines in background and send SSE when ready
        - generate_async=False: Block until guidelines generated (for testing)

        Guidelines are personalized using:
        - Parent's own words from stories
        - Specific people, places, toys mentioned
        - The hypothesis we're testing (internal, not revealed to parent)

        Returns guidelines in parent-facing format (no hypothesis revealed).
        """
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        # Find the cycle
        cycle = None
        for c in gestalt.exploration_cycles:
            if c.id == cycle_id:
                cycle = c
                break

        if not cycle:
            return {"error": "Exploration cycle not found"}

        if not cycle.video_appropriate:
            return {"error": "Video not appropriate for this exploration"}

        # Mark as accepted
        cycle.accept_video()

        # Set generating status
        cycle.guidelines_status = "generating"

        # Persist immediately so UI can show "generating" state
        await self._persist_gestalt(family_id, gestalt)

        if generate_async:
            # Start background task for guidelines generation
            import asyncio
            asyncio.create_task(
                self._generate_guidelines_background(family_id, cycle_id)
            )

            return {
                "status": "generating",
                "cycle_id": cycle_id,
                "message": "מכין הנחיות צילום מותאמות אישית...",
            }
        else:
            # Synchronous generation (for testing)
            scenarios = await self._generate_personalized_video_guidelines(gestalt, cycle)

            if not scenarios:
                return {"error": "Failed to generate video guidelines"}

            cycle.video_scenarios = scenarios
            cycle.guidelines_status = "ready"
            await self._persist_gestalt(family_id, gestalt)

            return {
                "status": "ready",
                "cycle_id": cycle_id,
                "guidelines": self._build_guidelines_response(gestalt, scenarios),
            }

    async def _generate_guidelines_background(self, family_id: str, cycle_id: str):
        """Background task to generate guidelines and send SSE when ready."""
        try:
            gestalt = await self._get_gestalt(family_id)
            if not gestalt:
                logger.error(f"Background guidelines: family {family_id} not found")
                return

            cycle = None
            for c in gestalt.exploration_cycles:
                if c.id == cycle_id:
                    cycle = c
                    break

            if not cycle:
                logger.error(f"Background guidelines: cycle {cycle_id} not found")
                return

            # Generate guidelines
            logger.info(f"🎬 Background generating guidelines for {family_id}/{cycle_id}")
            scenarios = await self._generate_personalized_video_guidelines(gestalt, cycle)

            if scenarios:
                cycle.video_scenarios = scenarios
                cycle.guidelines_status = "ready"
                await self._persist_gestalt(family_id, gestalt)

                # Send SSE to update cards
                from app.services.sse_notifier import get_sse_notifier
                updated_cards = self._derive_cards(gestalt)
                await get_sse_notifier().notify_cards_updated(family_id, updated_cards)

                logger.info(f"✅ Background guidelines ready for {family_id}/{cycle_id}")
            else:
                cycle.guidelines_status = "error"
                await self._persist_gestalt(family_id, gestalt)
                logger.error(f"❌ Background guidelines failed for {family_id}/{cycle_id}")

        except Exception as e:
            logger.error(f"Background guidelines error: {e}", exc_info=True)

    async def decline_video_suggestion(self, family_id: str, cycle_id: str) -> Dict[str, Any]:
        """
        Parent declined video suggestion.

        Respect their choice - don't ask again for this cycle.
        Continue exploring via conversation.
        """
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        for cycle in gestalt.exploration_cycles:
            if cycle.id == cycle_id:
                cycle.decline_video()
                await self._persist_gestalt(family_id, gestalt)
                return {
                    "status": "declined",
                    "cycle_id": cycle_id,
                    "message": "בסדר גמור! נמשיך להכיר דרך השיחה שלנו.",
                }

        return {"error": "Exploration cycle not found"}

    async def get_video_guidelines(self, family_id: str, cycle_id: str) -> Dict[str, Any]:
        """Get video guidelines for a cycle (parent-facing format only)."""
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        for cycle in gestalt.exploration_cycles:
            if cycle.id == cycle_id and cycle.video_scenarios:
                return self._build_guidelines_response(gestalt, cycle.video_scenarios)

        return {"error": "No video guidelines found for this cycle"}

    async def record_video_upload(
        self,
        family_id: str,
        scenario_id: str,
        file_path: str,
        duration_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Record that a video was uploaded for a scenario.

        Updates the scenario status to 'uploaded' and stores file path.
        This triggers card change from 'guidelines_ready' to 'video_uploaded'.

        scenario_id can be either:
        - The actual scenario ID (like "scenario_001")
        - The scenario title (like "מעבר מפעילות לפעילות")
        """
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        # Find the scenario across all cycles (by ID or title)
        for cycle in gestalt.exploration_cycles:
            for scenario in cycle.video_scenarios:
                # Match by ID or title
                if scenario.id == scenario_id or scenario.title == scenario_id:
                    scenario.status = "uploaded"
                    scenario.video_path = file_path  # Model uses video_path, not file_path
                    scenario.uploaded_at = datetime.now()

                    await self._persist_gestalt(family_id, gestalt)

                    logger.info(f"📹 Video uploaded for scenario '{scenario.title}' (id={scenario.id}) in cycle {cycle.id}")
                    return {
                        "status": "uploaded",
                        "scenario_id": scenario.id,
                        "scenario_title": scenario.title,
                        "cycle_id": cycle.id,
                        "message": "הסרטון התקבל! אפשר לנתח אותו כשתהיו מוכנים.",
                    }

        logger.warning(f"⚠️ Scenario not found: '{scenario_id}' in family {family_id}")
        logger.warning(f"   Available scenarios: {[(s.id, s.title) for c in gestalt.exploration_cycles for s in c.video_scenarios]}")
        return {"error": f"Scenario '{scenario_id}' not found"}

    def _build_guidelines_response(self, gestalt: LivingGestalt, scenarios: List) -> Dict[str, Any]:
        """Build parent-facing guidelines response."""
        child_name = gestalt.child_name or "הילד/ה"
        return {
            "child_name": child_name,
            "introduction": f"הסרטונים יעזרו לי לראות את {child_name} בסביבה הטבעית שלו ולהבין אותו טוב יותר.",
            "scenarios": [s.to_parent_facing_dict() for s in scenarios],
            "general_tips": [
                "צלמו בסביבה טבעית - בית, גן, או כל מקום שנוח לכם",
                "אורך מומלץ: 2-5 דקות לכל סרטון",
                f"אין צורך בהכנה מיוחדת - אנחנו רוצים לראות את {child_name} כמו שהוא",
                "תאורה טובה עוזרת, אבל לא חייבת להיות מושלמת",
            ],
        }

    async def _generate_personalized_video_guidelines(
        self,
        gestalt: LivingGestalt,
        cycle: "ExplorationCycle",
    ) -> List["VideoScenario"]:
        """
        Generate PERSONALIZED video guidelines using LLM.

        The LLM receives:
        - All stories we've captured (rich with context)
        - All facts about the child
        - The hypothesis we're testing (internal)
        - Child's strengths and interests

        The LLM generates:
        - Warm, concrete instructions using parent's own words
        - Specific people, places, toys from their stories
        - Sandwich rationale (validate → explain → reassure)

        Parent NEVER sees the hypothesis - only warm filming instructions.
        """
        from .models import VideoScenario
        from app.services.llm.factory import create_llm_provider
        from app.services.llm.base import Message as LLMMessage
        import json

        child_name = gestalt.child_name or "הילד/ה"

        # Build rich context from stories and facts
        stories_context = self._format_stories_for_llm(gestalt.stories)
        facts_context = self._format_facts_for_llm(gestalt.understanding.facts)
        strengths_context = self._extract_strengths(gestalt)

        # Build the prompt
        prompt = f"""# Generate Personalized Video Guidelines (Hebrew)

## Your Role
You are Chitta, a warm and supportive child development expert.
Write directly to the Israeli parent in natural Hebrew.

## CRITICAL: Use Their World
Extract from the stories and facts:
- **People** they mentioned (סבתא, הגננת, אח/אחות - use their names if given)
- **Places** in their life (הגן, מגרש המשחקים, הסלון, המטבח)
- **Toys/Objects** the child loves (specific toys, games, items mentioned)
- **Parent's own words** - mirror their language, not clinical terms

## Child Context
**Name:** {child_name}

## Stories Shared (RICH CONTEXT - USE THIS!)
{stories_context}

## Facts We Know
{facts_context}

## Strengths & Interests
{strengths_context}

## What We're Exploring (INTERNAL - DO NOT REVEAL TO PARENT)
**Focus:** {cycle.focus}
**Domain:** {cycle.focus_domain}
**Theory (if hypothesis):** {cycle.theory or "N/A"}
**Question (if question):** {cycle.question or "N/A"}

## Generate ONE Video Scenario

### Required Output (JSON):
{{
  "title": "Short Hebrew title - warm, not clinical",
  "what_to_film": "CONCRETE instructions using THEIR specific toys/places/people. Example: 'שבו ליד שולחן המטבח עם [הצעצוע שהם הזכירו]. שחקו יחד 5 דקות.'",
  "rationale_for_parent": "Sandwich structure: 1) Validate ('שמעתי ש...'), 2) Explain why this helps, 3) Reassure ('אל תדאגו מ...')",
  "duration_suggestion": "3-5 דקות",
  "example_situations": ["Situation 1 using their context", "Situation 2 using their context"],
  "focus_points": ["Internal analysis point 1 - NOT for parent", "Internal analysis point 2"],
  "what_we_hope_to_learn": "Clinical goal - NOT for parent"
}}

### Quality Checklist:
❌ BAD: "צלמו משחק" (too generic)
✅ GOOD: "שבו ליד השולחן במטבח, תנו ל{child_name} את הדינוזאורים שהוא אוהב, ושחקו יחד 5 דקות"

❌ BAD: "צלמו אינטראקציה חברתית" (clinical)
✅ GOOD: "כשסבתא מגיעה לביקור, צלמו כמה דקות של משחק יחד"

❌ BAD: Generic rationale
✅ GOOD: "שמעתי שהבקרים שלכם עמוסים ושקשה לו עם מעברים. לראות רגע כזה יעזור לי להבין בדיוק מה קורה ואיך אפשר לעזור. אל תנסו 'לסדר' את המצב - אנחנו רוצים לראות את המציאות."

Generate the scenario JSON now:
"""

        try:
            # Use STRONG LLM for guidelines generation (from STRONG_LLM_MODEL env var)
            llm = gestalt._get_strong_llm()
            response = await llm.chat(
                messages=[LLMMessage(role="user", content=prompt)],
                functions=None,
                temperature=0.7,
                max_tokens=2000,
            )

            # Parse the JSON response
            response_text = response.content or ""

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            scenario_data = json.loads(response_text)

            # Create VideoScenario from LLM response
            scenario = VideoScenario.create(
                title=scenario_data.get("title", "תצפית"),
                what_to_film=scenario_data.get("what_to_film", "צלמו מצב יומיומי טבעי"),
                rationale_for_parent=scenario_data.get("rationale_for_parent", ""),
                target_hypothesis_id=cycle.id,
                what_we_hope_to_learn=scenario_data.get("what_we_hope_to_learn", cycle.focus),
                focus_points=scenario_data.get("focus_points", []),
                duration_suggestion=scenario_data.get("duration_suggestion", "3-5 דקות"),
                example_situations=scenario_data.get("example_situations", []),
                category="hypothesis_test" if cycle.curiosity_type == "hypothesis" else "exploration",
            )

            logger.info(f"✅ Generated personalized video guidelines for cycle: {cycle.focus}")
            return [scenario]

        except Exception as e:
            logger.error(f"Error generating video guidelines: {e}")
            # Fallback to simple scenario
            return [self._create_fallback_scenario(gestalt, cycle)]

    def _format_stories_for_llm(self, stories: List) -> str:
        """Format stories for LLM context - preserve the richness."""
        if not stories:
            return "No stories captured yet."

        lines = []
        for story in stories[-5:]:  # Last 5 stories
            lines.append(f"- {story.summary}")
            if story.reveals:
                lines.append(f"  (Reveals: {', '.join(story.reveals[:3])})")
        return "\n".join(lines)

    def _format_facts_for_llm(self, facts: List) -> str:
        """Format facts for LLM context."""
        if not facts:
            return "Still getting to know this child."

        # Group by domain
        by_domain = {}
        for fact in facts:
            domain = fact.domain or "general"
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(fact.content)

        lines = []
        for domain, contents in by_domain.items():
            lines.append(f"**{domain}:** {'; '.join(contents[:3])}")
        return "\n".join(lines)

    def _extract_strengths(self, gestalt: LivingGestalt) -> str:
        """Extract strengths from facts and stories."""
        strength_facts = [
            f.content for f in gestalt.understanding.facts
            if f.domain in ["strengths", "essence", "interests"]
        ]
        if strength_facts:
            return "\n".join(f"- {s}" for s in strength_facts[:5])
        return "Not yet identified - explore through video."

    def _create_fallback_scenario(self, gestalt: LivingGestalt, cycle) -> "VideoScenario":
        """Create a simple fallback scenario if LLM fails."""
        from .models import VideoScenario
        child_name = gestalt.child_name or "הילד/ה"

        return VideoScenario.create(
            title="תצפית יומיומית",
            what_to_film=f"צלמו את {child_name} במצב יומיומי טבעי - משחק, אוכל, או אינטראקציה עם בני משפחה.",
            rationale_for_parent=f"לראות את {child_name} בסביבה הטבעית יעזור לי להבין אותו טוב יותר. אל תדאגו מ'לסדר' את המצב - אנחנו רוצים לראות את המציאות.",
            target_hypothesis_id=cycle.id,
            what_we_hope_to_learn=cycle.focus,
            focus_points=[f"בדיקת: {cycle.focus}"],
            duration_suggestion="3-5 דקות",
            example_situations=["משחק בבית", "ארוחה משפחתית"],
            category="exploration",
        )

    # ========================================
    # VIDEO UPLOAD & ANALYSIS
    # ========================================

    async def mark_video_uploaded(
        self,
        family_id: str,
        cycle_id: str,
        scenario_id: str,
        video_path: str,
    ) -> Dict[str, Any]:
        """
        Mark a video scenario as uploaded.

        Called after file is saved by the API endpoint.
        """
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        for cycle in gestalt.exploration_cycles:
            if cycle.id == cycle_id:
                scenario = cycle.get_scenario(scenario_id)
                if not scenario:
                    return {"error": "Scenario not found"}

                scenario.mark_uploaded(video_path)
                await self._persist_gestalt(family_id, gestalt)

                return {
                    "status": "uploaded",
                    "scenario_id": scenario_id,
                    "video_path": video_path,
                }

        return {"error": "Exploration cycle not found"}

    async def analyze_cycle_videos(
        self,
        family_id: str,
        cycle_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze all uploaded videos for a cycle.

        Uses sophisticated video analysis to:
        1. Analyze video with hypothesis-driven prompt
        2. Extract objective observations as evidence
        3. Update hypothesis confidence based on verdict
        4. Capture strengths (non-negotiable)
        5. Generate warm parent-facing insights

        Returns insights for the parent (no hypothesis revealed).
        """
        from .models import Evidence, TemporalFact

        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found"}

        cycle = None
        for c in gestalt.exploration_cycles:
            if c.id == cycle_id:
                cycle = c
                break

        if not cycle:
            return {"error": "Exploration cycle not found"}

        # Get uploaded (not yet analyzed) videos
        pending_scenarios = [s for s in cycle.video_scenarios if s.status == "uploaded"]
        if not pending_scenarios:
            return {"error": "No videos to analyze"}

        insights = []
        evidence_added = 0
        strengths_found = []
        confidence_before = cycle.confidence
        hypothesis_evidence = {}  # Initialize for return statement
        validation_failed_count = 0

        for scenario in pending_scenarios:
            # Analyze the video with sophisticated prompt
            analysis_result = await self._analyze_video(gestalt, cycle, scenario)

            if analysis_result:
                # Check if video validation failed
                video_validation = analysis_result.get("video_validation", {})
                is_usable = video_validation.get("is_usable", True)

                if not is_usable:
                    # Validation failed - mark as such, don't add evidence
                    scenario.mark_validation_failed(analysis_result)
                    validation_failed_count += 1
                    logger.warning(f"⚠️ Video validation failed for scenario {scenario.id}")
                    logger.warning(f"   Issues: {video_validation.get('validation_issues', [])}")
                    # Add a single insight about the failed validation
                    insights.append(
                        f"הסרטון שהועלה לא תואם לבקשה. "
                        f"{video_validation.get('what_video_shows', '')}. "
                        f"אפשר להעלות סרטון חדש."
                    )
                    continue  # Skip evidence processing for this scenario

                # Mark scenario as analyzed with full result
                scenario.mark_analyzed(analysis_result)

                # Create evidence from observations
                for observation in analysis_result.get("observations", []):
                    evidence = Evidence.create(
                        content=observation.get("content", ""),
                        effect=observation.get("effect", "supports"),
                        source="video",
                    )
                    cycle.add_evidence(evidence)
                    evidence_added += 1

                # Update confidence based on hypothesis_evidence verdict
                hypothesis_evidence = analysis_result.get("hypothesis_evidence", {})
                verdict = hypothesis_evidence.get("overall_verdict", "inconclusive")
                confidence_level = hypothesis_evidence.get("confidence_level", "Low")

                if cycle.curiosity_type == "hypothesis" and cycle.confidence is not None:
                    # More nuanced confidence update based on verdict
                    if verdict == "supports":
                        boost = 0.15 if confidence_level == "High" else 0.10 if confidence_level == "Moderate" else 0.05
                        cycle.confidence = min(1.0, cycle.confidence + boost)
                    elif verdict == "contradicts":
                        drop = 0.20 if confidence_level == "High" else 0.15 if confidence_level == "Moderate" else 0.10
                        cycle.confidence = max(0.0, cycle.confidence - drop)
                    elif verdict == "mixed":
                        # Mixed evidence - slight increase if more supports than contradicts
                        supporting = len(hypothesis_evidence.get("supporting_evidence", []))
                        contradicting = len(hypothesis_evidence.get("contradicting_evidence", []))
                        if supporting > contradicting:
                            cycle.confidence = min(1.0, cycle.confidence + 0.05)
                        elif contradicting > supporting:
                            cycle.confidence = max(0.0, cycle.confidence - 0.05)
                        # Equal: no change

                # Capture strengths as facts (strengths are GOLD)
                for strength in analysis_result.get("strengths_observed", []):
                    strength_fact = TemporalFact.from_observation(
                        content=strength.get("strength", ""),
                        domain="strengths",
                        confidence=0.8,  # High confidence from direct observation
                    )
                    gestalt.understanding.add_fact(strength_fact)
                    strengths_found.append(strength.get("strength", ""))

                # Add insights (parent-facing, no hypothesis)
                insights.extend(analysis_result.get("insights", []))

                # Log capacity revealed (valuable for understanding)
                capacity = hypothesis_evidence.get("capacity_revealed", {})
                if capacity.get("description"):
                    logger.info(f"💪 Capacity revealed: {capacity.get('description')}")

                # Capture new questions for future exploration
                new_questions = hypothesis_evidence.get("new_questions_raised", [])
                for question in new_questions:
                    logger.info(f"❓ New question from video: {question}")

        # Persist changes
        await self._persist_gestalt(family_id, gestalt)

        # Determine overall status
        if validation_failed_count == len(pending_scenarios):
            status = "validation_failed"
        elif validation_failed_count > 0:
            status = "partial"  # Some passed, some failed
        else:
            status = "analyzed"

        return {
            "status": status,
            "cycle_id": cycle_id,
            "insights": insights,
            "evidence_added": evidence_added,
            "strengths_found": strengths_found,
            "validation_failed_count": validation_failed_count,
            "confidence_update": {
                "before": confidence_before,
                "after": cycle.confidence,
                "verdict": hypothesis_evidence.get("overall_verdict", "unknown"),
            } if cycle.curiosity_type == "hypothesis" and hypothesis_evidence else None,
        }

    async def _analyze_video(
        self,
        gestalt: LivingGestalt,
        cycle,
        scenario,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single video using Gemini's video capabilities.

        Adapted from the original VideoAnalysisService with wisdom:
        - Hypothesis-driven: PRIMARY job is evidence for/against hypothesis
        - Strengths-based: ALWAYS find strengths (non-negotiable)
        - Objective Evidence Protocol: Signs vs Symptoms, Show Don't Tell
        - Vocabulary mirroring: Use parent's words from stories/facts
        - Living Gestalt: See the whole child, not just problems

        Returns:
        - observations: List of {content, effect, timestamp} for evidence
        - insights: Parent-facing insights (warm, no hypothesis revealed)
        - hypothesis_evidence: Detailed evidence assessment
        - strengths_observed: Documented strengths from video
        """
        import json
        import os
        from pathlib import Path

        child_name = gestalt.child_name or "הילד/ה"

        # Build context from gestalt
        stories_context = self._format_stories_for_llm(gestalt.stories)
        facts_context = self._format_facts_for_llm(gestalt.understanding.facts)
        strengths_context = self._extract_strengths(gestalt)

        # Extract vocabulary from stories (parent's words)
        vocab_examples = self._extract_vocabulary_from_stories(gestalt.stories)

        # Build the hypothesis-driven analysis prompt
        prompt = f"""# Role: Chitta - Hypothesis-Driven Video Analysis

**Role:** You are "Chitta," an expert AI child behavior analyst. Your framework combines **clinical observation standards** with **hypothesis-driven exploration** and **strengths-based developmental psychology**.

**Objective:** Analyze this video as part of an EXPLORATION CYCLE. Your primary job is to:
1. **Test the specific hypothesis** this video was designed to explore
2. **Provide evidence** - what supports or contradicts our working theories?
3. **See the whole child** - strengths, essence, and capacity alongside concerns

## Living Gestalt Philosophy

You see the WHOLE child, not just problems:
- **Essence first** - Who is this child? Temperament, energy, qualities
- **Strengths are data** - What they do well reveals capacity
- **Hypotheses are held lightly** - We're exploring, not confirming bias
- **Contradictions are gold** - When behavior doesn't fit, that's information

## VIDEO VALIDATION (CRITICAL - THIS IS A GATE!)

**STOP! Before ANY analysis, you MUST validate the video. If validation FAILS, you must NOT proceed with hypothesis testing.**

### Step 1: Scenario Match Check
Compare what was REQUESTED vs what was FILMED:
- **Requested:** "{scenario.what_to_film}"
- **Question:** Does the video show THIS scenario, or something completely different?

Examples of FAILED scenario match:
- Asked for "מעבר מפעילות לפעילות" but video shows child just playing/spinning
- Asked for "ארוחת בוקר" but video shows child at playground
- Asked for specific interaction but video shows unrelated activity

### Step 2: Child Verification Check
- Is ANY child visible in the video?
- If we know the child is ~3.5 years old, does the child in video match roughly?
- If the video shows a clearly different child (wrong age, different gender), this FAILS

### Step 3: GATE DECISION

**IF is_usable = false:**
- Set verdict to "inconclusive"
- Set confidence_level to "Low"
- Leave observations_for_evidence EMPTY []
- Leave supporting_evidence and contradicting_evidence EMPTY []
- Put ONE insight: "הסרטון שהועלה לא תואם למה שביקשנו לצלם. נא להעלות סרטון של [what was requested]"
- DO NOT analyze the video content for hypothesis evidence!

**IF is_usable = true:**
- Proceed with full analysis below

## Input Data

**Child Profile:**
- Name: **{child_name}**
- Known facts: {facts_context}

**Child's Strengths (IMPORTANT - document when you see these!):**
{strengths_context}

**Stories Shared by Parent (use their vocabulary!):**
{stories_context}

**Parent's Vocabulary to Mirror:**
{json.dumps(vocab_examples, ensure_ascii=False)}

## Hypothesis Being Tested (CRITICAL)

**Target Hypothesis:** {cycle.theory or cycle.focus}
**What We Hope to Learn:** {scenario.what_we_hope_to_learn}
**Focus Points (internal - what to look for):**
{chr(10).join(f'  - {fp}' for fp in scenario.focus_points)}

**Your PRIMARY TASK:** Provide evidence that helps confirm OR refute this hypothesis.
- What would we see if the hypothesis is TRUE?
- What would we see if it's FALSE?
- What do we actually observe?

## Video Assignment Context

**Title Given to Parent:** {scenario.title}
**Filming Instructions:** {scenario.what_to_film}
**Duration:** {scenario.duration_suggestion}

## CRITICAL: THE OBJECTIVE EVIDENCE PROTOCOL

You must strictly adhere to these rules when describing "Evidence":

1. **Signs vs. Symptoms:**
   - **Subjective (The Story):** "Child says they are upset." (This is narrative).
   - **Objective (The Observation):** "Child states 'I don't want to' while averting gaze, hunching shoulders, and lowering voice volume." (This is behavior).
   - **Rule:** NEVER accept a child's self-report as factual evidence. Instead, report the **act of saying it** and the **affect** shown.

2. **The "Show, Don't Tell" Rule:**
   - ❌ BAD: "Child was anxious"
   - ✅ GOOD: "Child bit lip, fidgeted with shirt hem, and had rapid breathing"

3. **Contextualize Speech:** If the evidence is verbal, describe the **prosody** (tone, volume, speed) and **accompanying gesture**.

4. **Use MM:SS Timestamps:** Every observation must include BOTH start and end times (e.g., "timestamp_start": "01:15", "timestamp_end": "01:23") to enable video clip extraction for reports

---

## Output JSON Structure

Return a valid JSON object with this structure.

**IMPORTANT: If video_validation.is_usable is FALSE, leave all evidence arrays EMPTY and set verdict to "inconclusive"!**

```json
{{
  "video_validation": {{
    "is_usable": "<boolean: FALSE if video doesn't match requested scenario or shows wrong child>",
    "scenario_matches": "<boolean: does video show what was requested in filming instructions?>",
    "what_video_shows": "<Brief description: 'ילד מסתובב על כיסא' not 'מעבר בין פעילויות'>",
    "child_visible": "<boolean: is child clearly visible?>",
    "child_appears_consistent": "<boolean: does child match expected age/profile?>",
    "validation_issues": ["<List specific issues: 'הסרטון מראה ילד משחק, לא מעבר בין פעילויות'>"],
    "recommendation": "<proceed_with_analysis|request_new_video>"
  }},

  "hypothesis_evidence": {{
    "// IMPORTANT": "If is_usable=false, set verdict=inconclusive, confidence=Low, and leave evidence arrays EMPTY",
    "target_hypothesis": "{cycle.theory or cycle.focus}",
    "overall_verdict": "<supports|contradicts|mixed|inconclusive>",
    "confidence_level": "<High|Moderate|Low>",
    "reasoning": "<2-3 sentences explaining what the video tells us about the hypothesis>",
    "supporting_evidence": [
      {{
        "observation": "<Specific behavior using parent's vocabulary>",
        "timestamp_start": "<MM:SS - when behavior starts>",
        "timestamp_end": "<MM:SS - when behavior ends>",
        "why_this_supports": "<Explain the connection>"
      }}
    ],
    "contradicting_evidence": [
      {{
        "observation": "<Specific behavior that contradicts>",
        "timestamp_start": "<MM:SS - when behavior starts>",
        "timestamp_end": "<MM:SS - when behavior ends>",
        "why_this_contradicts": "<Explain>"
      }}
    ],
    "capacity_revealed": {{
      "description": "<What capacity did the child demonstrate?>",
      "conditions_that_enabled_it": "<What conditions allowed this?>"
    }},
    "new_questions_raised": ["<Questions that emerged>"]
  }},

  "observations_for_evidence": [
    {{
      "content": "<Objective observation in Hebrew using parent's vocabulary>",
      "effect": "<supports|contradicts|transforms>",
      "timestamp_start": "<MM:SS - when behavior starts>",
      "timestamp_end": "<MM:SS - when behavior ends>",
      "domain": "<social|emotional|motor|cognitive|sensory|regulation>"
    }}
  ],

  "strengths_observed": [
    {{
      "strength": "<What the child did well>",
      "timestamp_start": "<MM:SS - when behavior starts>",
      "timestamp_end": "<MM:SS - when behavior ends>",
      "clinical_value": "<Why this matters developmentally>"
    }}
  ],

  "parent_facing_insights": [
    "<Warm insight 1 - NO hypothesis revealed, uses their vocabulary>",
    "<Warm insight 2 - focuses on what you SAW the child do>"
  ],

  "holistic_summary": {{
    "temperament_observed": "<What temperament qualities showed?>",
    "regulation_state": "<Regulated|Hypoaroused|Hyperaroused|Fluctuating>",
    "parent_child_dynamic": "<What did you notice about their interaction?>"
  }},

  "focus_point_findings": [
    {{
      "focus_point": "<From scenario.focus_points>",
      "finding": "<What we observed>",
      "confidence": "<High|Moderate|Low>"
    }}
  ],

  "suggested_next_steps": [
    {{
      "type": "<conversation|video|observation>",
      "description": "<What to explore next>",
      "why": "<Why this would help>"
    }}
  ]
}}
```

**CRITICAL REMINDERS:**
1. **VALIDATION IS A GATE** - If video doesn't match scenario, set is_usable=false and DO NOT analyze!
2. Use parent's vocabulary when describing behaviors
3. ALWAYS find strengths - this is NON-NEGOTIABLE (only if video is usable)
4. Use MM:SS format for all timestamps - include BOTH start AND end times for each observation
5. The parent NEVER sees the hypothesis - insights must be warm and general
6. Contradictions are valuable - if behavior doesn't match hypothesis, that's data
7. Return ONLY valid JSON, no additional text
8. **TIMESTAMPS ARE CRITICAL** - Each observation needs timestamp_start AND timestamp_end for video evidence in reports

**EXAMPLE OF FAILED VALIDATION:**
If asked to film "מעבר מפעילות לפעילות" but video shows child spinning on chair:
- is_usable: false
- scenario_matches: false
- what_video_shows: "ילד מסתובב על כיסא"
- validation_issues: ["הסרטון לא מראה מעבר בין פעילויות - מראה ילד משחק על כיסא"]
- verdict: "inconclusive"
- observations_for_evidence: []
- parent_facing_insights: ["הסרטון שהועלה לא תואם למה שביקשנו לצלם. נא להעלות סרטון של מעבר בין פעילויות."]
"""

        try:
            # Resolve video path - handle both relative and absolute paths
            from pathlib import Path as PathLib
            video_path = scenario.video_path
            if video_path and not os.path.isabs(video_path):
                # Relative path - resolve from backend directory
                backend_dir = PathLib(__file__).parent.parent.parent  # chitta/service.py -> chitta -> app -> backend
                video_path = str(backend_dir / video_path)

            # Check if video file exists
            if not video_path or not os.path.exists(video_path):
                logger.warning(f"Video file not found: {video_path} (original: {scenario.video_path})")
                return self._create_simulated_analysis(child_name, cycle, scenario)

            # Use Gemini's video analysis capability
            from google import genai
            from google.genai import types

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY not found")
                return self._create_simulated_analysis(child_name, cycle, scenario)

            client = genai.Client(api_key=api_key)

            # Upload video to Gemini File API
            logger.info(f"📤 Uploading video to Gemini: {video_path}")
            uploaded_file = client.files.upload(file=video_path)

            # Wait for processing
            import time
            max_wait = 60
            wait_time = 0
            while uploaded_file.state == "PROCESSING" and wait_time < max_wait:
                logger.info(f"   Processing video... ({wait_time}s)")
                time.sleep(3)
                wait_time += 3
                uploaded_file = client.files.get(name=uploaded_file.name)

            if uploaded_file.state != "ACTIVE":
                logger.error(f"Video processing failed: {uploaded_file.state}")
                return self._create_simulated_analysis(child_name, cycle, scenario)

            logger.info("🤖 Analyzing video with Gemini...")

            # Send video + prompt for analysis (use STRONG model from env)
            strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-2.5-pro")
            logger.info(f"🎥 Using strong model for video analysis: {strong_model}")
            response = client.models.generate_content(
                model=strong_model,
                contents=[
                    uploaded_file,
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=6000,
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True,
                        maximum_remote_calls=0
                    )
                )
            )

            # Extract content from response
            content = ""
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                content += part.text

            if not content:
                logger.error("Empty response from Gemini")
                return self._create_simulated_analysis(child_name, cycle, scenario)

            # Parse JSON response
            result = json.loads(content)

            # Transform to our internal format
            return self._transform_analysis_result(result)

        except Exception as e:
            logger.error(f"Error analyzing video: {e}", exc_info=True)
            return self._create_simulated_analysis(child_name, cycle, scenario)

    def _extract_vocabulary_from_stories(self, stories: List) -> Dict[str, str]:
        """Extract vocabulary patterns from parent's stories."""
        vocab = {}
        for story in stories[-5:]:
            # Simple extraction - in production would use NLP
            if "מרחף" in story.summary:
                vocab["מרחף"] = "לתאר קשיי קשב"
            if "מתפרץ" in story.summary:
                vocab["מתפרץ"] = "לתאר התנהגות אימפולסיבית"
            if "נסגר" in story.summary:
                vocab["נסגר"] = "לתאר נסיגה חברתית"
        return vocab

    def _transform_analysis_result(self, result: Dict) -> Dict[str, Any]:
        """Transform Gemini analysis to our internal format."""
        # Check video validation first
        video_validation = result.get("video_validation", {})
        is_usable = video_validation.get("is_usable", True)
        validation_issues = video_validation.get("validation_issues", [])

        if not is_usable or validation_issues:
            logger.warning(f"⚠️ Video validation issues: {validation_issues}")
            logger.warning(f"   What video shows: {video_validation.get('what_video_shows', 'unknown')}")
            logger.warning(f"   Recommendation: {video_validation.get('recommendation', 'unknown')}")

        # Extract observations for evidence
        observations = []
        for obs in result.get("observations_for_evidence", []):
            observations.append({
                "content": obs.get("content", ""),
                "effect": obs.get("effect", "supports"),
                "timestamp_start": obs.get("timestamp_start", obs.get("timestamp", "")),  # fallback for old format
                "timestamp_end": obs.get("timestamp_end", ""),
                "domain": obs.get("domain", "general"),
            })

        # Extract parent-facing insights
        insights = result.get("parent_facing_insights", [])

        # If validation failed, add a note to insights
        if not is_usable and validation_issues:
            insights = [f"שים לב: הסרטון שהועלה לא תואם לבקשה - {', '.join(validation_issues)}"] + insights

        # Extract hypothesis evidence for cycle update
        hypothesis_evidence = result.get("hypothesis_evidence", {})

        # If validation failed, override verdict to inconclusive
        if not is_usable:
            hypothesis_evidence["overall_verdict"] = "inconclusive"
            hypothesis_evidence["confidence_level"] = "Low"
            hypothesis_evidence["reasoning"] = f"Video validation failed: {', '.join(validation_issues) if validation_issues else 'unknown issue'}"

        # Extract strengths
        strengths = result.get("strengths_observed", [])

        # Determine verdict for insights view (parent-facing)
        verdict = "inconclusive"
        if is_usable:
            verdict = hypothesis_evidence.get("overall_verdict", "inconclusive")

        return {
            "observations": observations,
            "insights": insights,
            "hypothesis_evidence": hypothesis_evidence,
            "strengths_observed": strengths,
            "holistic_summary": result.get("holistic_summary", {}),
            "focus_point_findings": result.get("focus_point_findings", []),
            "suggested_next_steps": result.get("suggested_next_steps", []),
            # Video validation info for insights view
            "video_validation": video_validation,
            "verdict": verdict,
            "confidence_level": hypothesis_evidence.get("confidence_level", "Low"),
            # Parent-facing insight list
            "insights_for_parent": insights,
        }

    def _create_simulated_analysis(
        self,
        child_name: str,
        cycle,
        scenario,
    ) -> Dict[str, Any]:
        """Create simulated analysis when video cannot be processed."""
        return {
            "observations": [{
                "content": f"צפיתי בסרטון של {child_name} - ניתוח מלא יתבצע כשהקובץ יהיה זמין",
                "effect": "neutral",
                "timestamp_start": "00:00",
                "timestamp_end": "00:00",
                "domain": "general",
            }],
            "insights": [
                f"קיבלתי את הסרטון של {child_name}. אעבור עליו בקרוב ואשתף תובנות.",
            ],
            "hypothesis_evidence": {
                "target_hypothesis": cycle.theory or cycle.focus,
                "overall_verdict": "inconclusive",
                "confidence_level": "Low",
                "reasoning": "ניתוח הסרטון בהמתנה",
                "supporting_evidence": [],
                "contradicting_evidence": [],
            },
            "strengths_observed": [],
            "holistic_summary": {},
            "focus_point_findings": [],
            "suggested_next_steps": [],
        }

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

    # ========================================
    # CHILD SPACE - FULL DATA FOR NEW UI
    # ========================================

    def derive_child_space_full(self, gestalt: LivingGestalt) -> Dict[str, Any]:
        """
        Derive complete ChildSpace data for the Living Portrait UI.

        Returns data for all four tabs:
        - essence: The living portrait (narrative, strengths, explorations, facts)
        - discoveries: Timeline of discovery milestones
        - observations: Video gallery with AI insights
        - share: Sharing options and status
        """
        return {
            "child_name": gestalt.child_name,
            "essence": self._derive_essence(gestalt),
            "discoveries": self._derive_discoveries(gestalt),
            "observations": self._derive_observations(gestalt),
            "share": self._derive_share_options(gestalt),
        }

    def _derive_essence(self, gestalt: LivingGestalt) -> Dict[str, Any]:
        """
        Derive the Essence tab - the living portrait.

        REQUIRES Crystal to exist - the route ensures this via ensure_crystal_fresh().
        Crystal provides:
        - Essence narrative, temperament, core qualities
        - Cross-domain patterns
        - Intervention pathways

        This is the HOLISTIC view of the child - not fragments, but connections.
        """
        # Check Crystal status
        has_crystal = hasattr(gestalt, 'crystal') and gestalt.crystal is not None
        is_crystal_stale = has_crystal and gestalt.is_crystal_stale()

        # === 1. ESSENCE NARRATIVE ===
        # Crystal is required - route ensures it exists
        narrative = None
        temperament = []
        core_qualities = []

        if has_crystal:
            crystal = gestalt.crystal
            narrative = crystal.essence_narrative
            temperament = crystal.temperament or []
            core_qualities = crystal.core_qualities or []

        # === 2. CROSS-DOMAIN PATTERNS ===
        patterns = []

        if has_crystal:
            for pattern in gestalt.crystal.patterns:
                patterns.append({
                    "description": pattern.description,
                    "domains": pattern.domains_involved,
                    "confidence": pattern.confidence,
                })

        # === 3. STRENGTHS & INTERESTS ===
        # Always derive from facts (these are observed, not synthesized)
        strengths = []
        interests = []

        for fact in gestalt.understanding.facts:
            if fact.domain == "strengths":
                strengths.append({
                    "domain": self._infer_strength_domain(fact.content),
                    "title_he": self._extract_strength_title(fact.content),
                    "content": fact.content,
                    "source": fact.source,
                })
            elif fact.domain == "interests":
                interests.append({
                    "content": fact.content,
                    "source": fact.source,
                })

        # Add strengths from video observations
        for cycle in gestalt.exploration_cycles:
            for scenario in cycle.video_scenarios:
                if scenario.analysis_result and scenario.status == "analyzed":
                    for strength in scenario.analysis_result.get("strengths_observed", []):
                        strength_text = strength.get("strength", "") if isinstance(strength, dict) else strength
                        if strength_text:
                            strengths.append({
                                "domain": "observed",
                                "title_he": strength_text,
                                "content": f"נצפה בסרטון: {scenario.title}",
                                "source": "video",
                            })

        # === 4. INTERVENTION PATHWAYS ===
        # Crystal is required - route ensures it exists
        intervention_pathways = []

        if has_crystal:
            for pathway in gestalt.crystal.intervention_pathways:
                intervention_pathways.append({
                    "hook": pathway.hook,
                    "concern": pathway.concern,
                    "suggestion": pathway.suggestion,
                    "confidence": pathway.confidence,
                })

        # === 5. ACTIVE EXPLORATIONS ===
        # Always derive from exploration_cycles (live data)
        active_explorations = []
        for cycle in gestalt.exploration_cycles:
            if cycle.status == "active":
                evidence_list = [
                    {"content": ev.content, "effect": ev.effect, "source": ev.source}
                    for ev in cycle.evidence
                ]
                has_video_pending = any(
                    s.status in ("pending", "uploaded") and s.video_path
                    for s in cycle.video_scenarios
                )
                has_video_analyzed = any(s.status == "analyzed" for s in cycle.video_scenarios)

                active_explorations.append({
                    "id": cycle.id,
                    "question": cycle.focus,
                    "theory": cycle.theory,
                    "confidence": cycle.confidence or 0.5,
                    "evidence_count": len(cycle.evidence),
                    "evidence": evidence_list,
                    "has_video_pending": has_video_pending,
                    "has_video_analyzed": has_video_analyzed,
                    "video_appropriate": cycle.video_appropriate,
                })

        # === 6. FACTS BY DOMAIN (secondary - parent knows these) ===
        facts_by_domain = {}
        for fact in gestalt.understanding.facts:
            domain = fact.domain or "general"
            # Skip strengths and interests - already shown prominently
            if domain in ("strengths", "interests"):
                continue
            if domain not in facts_by_domain:
                facts_by_domain[domain] = []
            facts_by_domain[domain].append(fact.content)

        # === 7. OPEN QUESTIONS ===
        # Crystal is required - route ensures it exists
        open_questions = []
        if has_crystal:
            open_questions = gestalt.crystal.open_questions or []

        # === 8. EXPERT RECOMMENDATIONS ===
        # NON-OBVIOUS professional matches based on who this child is
        expert_recommendations = []
        if has_crystal:
            for rec in gestalt.crystal.expert_recommendations or []:
                expert_recommendations.append({
                    "profession": rec.profession,
                    "specialization": rec.specialization,
                    "why_this_match": rec.why_this_match,
                    "recommended_approach": rec.recommended_approach,
                    "why_this_approach": rec.why_this_approach,
                    "what_to_look_for": rec.what_to_look_for,
                    "summary_for_professional": rec.summary_for_professional,
                    "confidence": rec.confidence,
                    "priority": rec.priority,
                })

        # Determine narrative status
        narrative_status = "available" if narrative else "forming"
        if is_crystal_stale:
            narrative_status = "updating"  # Signal to UI that update is in progress

        return {
            # PRIMARY - the holistic understanding (from Crystal)
            "narrative": narrative,
            "narrative_status": narrative_status,
            "temperament": temperament,
            "core_qualities": core_qualities,

            # PATTERNS - cross-domain connections (from Crystal)
            "patterns": patterns,

            # INTERVENTION PATHWAYS - how to reach/help the child (from Crystal)
            "intervention_pathways": intervention_pathways,
            "interests": interests[:4],  # The hooks

            # EXPERT RECOMMENDATIONS - NON-OBVIOUS professional matches (from Crystal)
            "expert_recommendations": expert_recommendations,

            # STRENGTHS - capabilities (from observed facts)
            "strengths": strengths[:6],

            # EXPLORATIONS - active curiosities (live data)
            "active_explorations": active_explorations,

            # OPEN QUESTIONS - what we still wonder (from Crystal)
            "open_questions": open_questions,

            # FACTS - secondary (grouped, for context)
            "facts_by_domain": facts_by_domain,

            # METADATA - Crystal status for UI
            "crystal_status": {
                "has_crystal": has_crystal,
                "is_stale": is_crystal_stale,
                "version": gestalt.crystal.version if has_crystal else 0,
            },
        }

    def _derive_intervention_pathways(
        self,
        gestalt: LivingGestalt,
        strengths: List[Dict],
        interests: List[Dict],
        patterns: List[Dict],
    ) -> List[Dict[str, Any]]:
        """
        Derive intervention pathways - how strengths/interests can address concerns.

        This is the KEY VALUE: connecting what lights them up to how to help them.
        Example: "Music/rhythm → Use singing for transitions"
        """
        pathways = []

        # Get concerns from exploration cycles
        concerns = []
        for cycle in gestalt.exploration_cycles:
            if cycle.status == "active" and cycle.curiosity_type in ("hypothesis", "question"):
                concerns.append({
                    "focus": cycle.focus,
                    "domain": cycle.focus_domain,
                })

        # Get interests and strengths as potential hooks
        hooks = []
        for interest in interests:
            hooks.append(interest.get("content", ""))
        for strength in strengths:
            hooks.append(strength.get("content", "") or strength.get("title_he", ""))

        # Simple heuristic matching for now
        # In the future, this could be LLM-generated during synthesis
        pathway_mappings = {
            "מוזיקה": ["מעברים", "ויסות", "רגשי"],
            "קצב": ["מעברים", "ויסות", "רגשי"],
            "דינוזאורים": ["חברתי", "משחק", "שפה"],
            "בנייה": ["מוטורי", "קוגניטיבי", "ריכוז"],
            "משחק": ["חברתי", "רגשי"],
            "סיפורים": ["שפה", "חברתי", "דמיון"],
            "תנועה": ["ויסות", "חושי"],
        }

        for hook in hooks:
            hook_lower = hook.lower() if hook else ""
            for keyword, helps_with in pathway_mappings.items():
                if keyword in hook_lower:
                    for concern in concerns:
                        concern_domain = concern.get("domain", "").lower()
                        if any(h in concern_domain for h in helps_with):
                            pathways.append({
                                "hook": hook,
                                "concern": concern.get("focus", ""),
                                "suggestion": f"אפשר להשתמש ב{keyword} כדי לעזור עם {concern.get('focus', '')}",
                            })

        # Deduplicate
        seen = set()
        unique_pathways = []
        for p in pathways:
            key = (p.get("hook", ""), p.get("concern", ""))
            if key not in seen:
                seen.add(key)
                unique_pathways.append(p)

        return unique_pathways[:5]  # Limit to top 5

    def _derive_discoveries(self, gestalt: LivingGestalt) -> Dict[str, Any]:
        """Derive the Discoveries tab - journey timeline."""
        milestones = []

        # Add journal entries as milestones
        for entry in gestalt.journal:
            milestone_type = "insight"
            if "התחלנו" in entry.summary or "הכרנו" in entry.summary:
                milestone_type = "started"
            elif "חקרנו" in entry.summary or "בדקנו" in entry.summary:
                milestone_type = "exploration_began"

            milestones.append({
                "id": f"journal_{entry.timestamp.isoformat()}",
                "timestamp": entry.timestamp.isoformat(),
                "type": milestone_type,
                "title_he": entry.summary,
                "description_he": ", ".join(entry.learned) if entry.learned else "",
                "significance": "major" if entry.significance == "notable" else "normal",
            })

        # Add video analyses as milestones
        for cycle in gestalt.exploration_cycles:
            for scenario in cycle.video_scenarios:
                if scenario.status == "analyzed" and scenario.analyzed_at:
                    # Find key insight from analysis
                    insights = []
                    if scenario.analysis_result:
                        insights = scenario.analysis_result.get("insights", [])
                    description = insights[0] if insights else "ניתוח הסרטון הושלם"

                    milestones.append({
                        "id": f"video_{scenario.id}",
                        "timestamp": scenario.analyzed_at.isoformat(),
                        "type": "video_analyzed",
                        "title_he": f"צפינו: {scenario.title}",
                        "description_he": description if isinstance(description, str) else "",
                        "video_id": scenario.id,
                        "exploration_id": cycle.id,
                        "significance": "major",
                    })

        # Sort by timestamp, newest first
        milestones.sort(key=lambda m: m["timestamp"], reverse=True)

        # Calculate stats
        days_since_start = 0
        if gestalt.journal:
            first_entry = min(gestalt.journal, key=lambda e: e.timestamp)
            days_since_start = (datetime.now() - first_entry.timestamp).days

        total_videos = sum(
            len([s for s in c.video_scenarios if s.video_path])
            for c in gestalt.exploration_cycles
        )

        insights_count = len([
            s for c in gestalt.exploration_cycles
            for s in c.video_scenarios
            if s.status == "analyzed"
        ])

        return {
            "milestones": milestones[:20],  # Limit for UI
            "days_since_start": days_since_start,
            "total_conversations": len(gestalt.journal),
            "total_videos": total_videos,
            "insights_discovered": insights_count,
        }

    def _derive_observations(self, gestalt: LivingGestalt) -> Dict[str, Any]:
        """Derive the Observations tab - video gallery."""
        videos = []

        for cycle in gestalt.exploration_cycles:
            for scenario in cycle.video_scenarios:
                if scenario.video_path:  # Has uploaded video
                    observations = []
                    strengths = []
                    insights = []

                    if scenario.analysis_result and scenario.status == "analyzed":
                        # Extract observations
                        for obs in scenario.analysis_result.get("observations", []):
                            observations.append({
                                "content": obs.get("content", ""),
                                "timestamp_start": obs.get("timestamp_start", obs.get("timestamp", "")),
                                "timestamp_end": obs.get("timestamp_end", ""),
                                "domain": obs.get("domain", "general"),
                                "effect": obs.get("effect", "neutral"),
                            })

                        # Extract strengths
                        for s in scenario.analysis_result.get("strengths_observed", []):
                            if isinstance(s, dict):
                                strengths.append(s.get("strength", ""))
                            elif isinstance(s, str):
                                strengths.append(s)

                        # Extract insights
                        insights = scenario.analysis_result.get("insights", [])

                    videos.append({
                        "id": scenario.id,
                        "title": scenario.title,
                        "video_path": scenario.video_path,
                        "duration_seconds": 0,  # TODO: extract from video
                        "uploaded_at": scenario.uploaded_at.isoformat() if scenario.uploaded_at else None,
                        "status": scenario.status,
                        "analyzed_at": scenario.analyzed_at.isoformat() if scenario.analyzed_at else None,
                        "hypothesis_title": cycle.theory or cycle.focus,
                        "hypothesis_id": cycle.id,
                        "observations": observations,
                        "strengths_observed": strengths,
                        "insights": insights,
                    })

        # Sort by upload date, newest first
        videos.sort(
            key=lambda v: v["uploaded_at"] or "1970-01-01",
            reverse=True
        )

        analyzed = sum(1 for v in videos if v["status"] == "analyzed")
        pending = sum(1 for v in videos if v["status"] in ["pending", "uploaded"])

        return {
            "videos": videos,
            "total_videos": len(videos),
            "analyzed_count": analyzed,
            "pending_count": pending,
        }

    def _derive_share_options(self, gestalt: LivingGestalt) -> Dict[str, Any]:
        """Derive the Share tab options."""
        # Check if we have enough understanding to share
        has_facts = len(gestalt.understanding.facts) >= 3
        has_exploration = len(gestalt.exploration_cycles) > 0
        can_generate = has_facts and has_exploration

        not_ready_reason = None
        if not can_generate:
            if not has_facts:
                not_ready_reason = "עדיין לא צברנו מספיק מידע. המשיכו לשוחח איתנו."
            else:
                not_ready_reason = "נשמח להכיר את הילד קצת יותר לפני שנוכל לשתף."

        return {
            "can_generate": can_generate,
            "not_ready_reason": not_ready_reason,
            "previous_summaries": [],  # TODO: Store and retrieve
        }

    def _infer_strength_domain(self, content: str) -> str:
        """Infer strength domain from content."""
        content_lower = content.lower()
        if any(word in content_lower for word in ["מוזיקה", "שיר", "שר"]):
            return "music"
        if any(word in content_lower for word in ["יצירתי", "בונה", "ציור"]):
            return "creativity"
        if any(word in content_lower for word in ["התמדה", "לא מוותר", "מנסה"]):
            return "persistence"
        if any(word in content_lower for word in ["חברתי", "חברים", "משחק עם"]):
            return "social"
        if any(word in content_lower for word in ["מוטורי", "רץ", "קופץ"]):
            return "motor"
        return "default"

    def _extract_strength_title(self, content: str) -> str:
        """Extract a short title from strength content."""
        # Take first few words or truncate
        words = content.split()
        if len(words) <= 4:
            return content
        return " ".join(words[:4]) + "..."

    async def generate_shareable_summary(
        self,
        family_id: str,
        recipient_type: str,
        recipient_subtype: str,
        time_available: str = "standard",
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a shareable summary adapted for the recipient.

        CRITICAL PHILOSOPHY:
        - Parent already knows the facts - they told us!
        - What they need is SYNTHESIS: patterns, connections, guidance
        - Strengths are intervention pathways, not just nice-to-knows
        - Every summary should answer: "Who is this child and how do we help them?"
        """
        gestalt = await self._get_gestalt(family_id)
        if not gestalt:
            return {"error": "Family not found", "content": ""}

        # Get voice profile based on recipient type
        profile = self._get_voice_profile(recipient_subtype or recipient_type)

        # Build gestalt summary for prompt
        child_name = gestalt.child_name or "הילד/ה"

        # Get essence narrative
        essence_narrative = ""
        if gestalt.understanding.essence and gestalt.understanding.essence.narrative:
            essence_narrative = gestalt.understanding.essence.narrative

        # Get patterns (cross-domain connections)
        patterns_summary = []
        if gestalt.understanding.patterns:
            for pattern in gestalt.understanding.patterns:
                domains_text = ", ".join(pattern.domains_involved) if pattern.domains_involved else ""
                patterns_summary.append(f"- {pattern.description} (מתחברים: {domains_text})")

        # Get strengths and interests (intervention hooks)
        strengths = []
        interests = []
        for fact in gestalt.understanding.facts:
            if fact.domain == "strengths":
                strengths.append(fact.content)
            elif fact.domain == "interests":
                interests.append(fact.content)

        # Get concerns/explorations
        concerns = []
        for cycle in gestalt.exploration_cycles:
            if cycle.status == "active":
                concerns.append({
                    "focus": cycle.focus,
                    "theory": cycle.theory or "בבדיקה",
                    "domain": cycle.focus_domain,
                })

        # Build intervention pathways hint
        pathways_hint = self._build_pathways_hint(strengths, interests, concerns)

        # Core facts (briefly, for context)
        core_facts = []
        for fact in gestalt.understanding.facts[:10]:
            if fact.domain not in ("strengths", "interests"):
                core_facts.append(f"- {fact.content}")

        # Build the prompt with HOLISTIC focus
        prompt = f"""# Generate Holistic Summary (Hebrew)

אתה עוזר להורה לשתף את ההבנה ההוליסטית על הילד עם {profile['name_he']}.

## העיקרון המנחה
הסיכום לא צריך לחזור על עובדות שההורה כבר יודע.
מה שההורה צריך הוא:
1. **מי הילד הזה כבן-אדם שלם** - לא רק הקשיים
2. **דפוסים שמחברים** - איפה רואים את אותו דבר במקומות שונים
3. **דרכי התערבות** - איך החוזקות והתחומי עניין יכולים לעזור עם הקשיים
4. **המלצות קונקרטיות** - מה לעשות, לא רק מה לדעת

## מידע על הילד

**שם:** {child_name}

**מי הוא (תמצית):**
{essence_narrative if essence_narrative else "עדיין מתגבשת תמונה"}

**חוזקות ותחומי עניין (אלה הם הכלים שלנו!):**
חוזקות: {', '.join(strengths) if strengths else 'בבדיקה'}
מה מדליק אותו: {', '.join(interests) if interests else 'בבדיקה'}

**דפוסים שזיהינו (מה מתחבר בין תחומים):**
{chr(10).join(patterns_summary) if patterns_summary else 'עדיין מזהים דפוסים'}

**קשיים/תחומים שאנחנו חוקרים:**
{chr(10).join([f"- {c['focus']}: {c['theory']}" for c in concerns]) if concerns else 'לא הוגדרו קשיים ספציפיים'}

**דרכי התערבות אפשריות (חיבור חוזקות לקשיים):**
{pathways_hint if pathways_hint else 'יש לחשוב איך להשתמש בחוזקות לעזור עם הקשיים'}

**עובדות רקע (בקצרה):**
{chr(10).join(core_facts[:5]) if core_facts else 'אין עובדות נוספות'}

## פרופיל הנמען
**סוג:** {profile['name_he']}
**רמת פירוט:** {profile['detail_level']}
**זמן זמין:** {time_available}

{f"## הקשר נוסף מההורה: {additional_context}" if additional_context else ""}

## הנחיות לכתיבה

**מבנה מומלץ:**
1. פתיחה עם מי הילד (לא עם הבעיה) - פסקה אחת חמה
2. הדפוסים שראינו - מה מתחבר, לא רשימת סימפטומים
3. החוזקות כדרכי התערבות - "הוא אוהב X, אז אפשר להשתמש בזה עבור Y"
4. המלצות קונקרטיות - מה לעשות בפועל
5. שאלות פתוחות (אם רלוונטי לנמען)

**סגנון:**
{"- השתמש במינוח קליני מקצועי" if profile.get('include_clinical_hints', False) else "- השתמש בשפה פשוטה ונגישה"}
{"- התחל עם החוזקות" if profile.get('include_strengths_first', True) else ""}
{"- כלול המלצות מעשיות" if profile.get('include_practical_strategies', True) else ""}
- כתוב בעברית חמה וטבעית, לא רובוטית
- **חשוב:** אל תסתפק ברשימת עובדות - חבר, נתח, הנחה

כתוב את הסיכום עכשיו:
"""

        try:
            # Use strong model
            from app.services.llm.factory import create_llm_provider
            from app.services.llm.base import Message as LLMMessage

            llm = gestalt._get_strong_llm()
            response = await llm.chat(
                messages=[LLMMessage(role="user", content=prompt)],
                functions=None,
                temperature=0.7,
                max_tokens=6000,  # Hebrew summaries need more tokens to avoid truncation
            )

            content = response.content or ""
            return {
                "content": content,
                "recipient_type": recipient_type,
                "recipient_subtype": recipient_subtype,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating shareable summary: {e}")
            return {
                "error": str(e),
                "content": f"לצערנו לא הצלחנו ליצור סיכום. נסו שוב מאוחר יותר.",
            }

    def _build_pathways_hint(
        self,
        strengths: List[str],
        interests: List[str],
        concerns: List[Dict],
    ) -> str:
        """
        Build intervention pathways hint for LLM.

        Shows how strengths/interests can connect to concerns.
        """
        if not concerns or (not strengths and not interests):
            return ""

        hints = []
        all_hooks = strengths + interests

        # Simple mapping of interest keywords to potential intervention areas
        pathway_mappings = {
            "מוזיקה": "מעברים, ויסות רגשי",
            "קצב": "מעברים, ויסות",
            "דינוזאורים": "משחק חברתי, שפה",
            "בנייה": "מוטוריקה עדינה, ריכוז",
            "משחק": "קשר חברתי",
            "סיפורים": "שפה, חברתי",
            "תנועה": "ויסות חושי",
            "ציור": "הבעה רגשית, מוטוריקה",
            "חיות": "קשר, אמפתיה",
        }

        for hook in all_hooks:
            if not hook:
                continue
            hook_lower = hook.lower()
            for keyword, helps in pathway_mappings.items():
                if keyword in hook_lower:
                    hints.append(f"- {hook} → יכול לעזור עם: {helps}")
                    break

        return "\n".join(hints[:5]) if hints else ""

    def _get_voice_profile(self, profile_id: str) -> Dict[str, Any]:
        """Get voice profile configuration."""
        profiles = {
            "neurologist": {
                "name_he": "נוירולוג",
                "terminology": "clinical",
                "detail_level": "dense",
                "include_clinical_hints": True,
                "include_practical_strategies": False,
                "include_strengths_first": False,
                "include_open_questions": True,
            },
            "psychologist": {
                "name_he": "פסיכולוג",
                "terminology": "clinical",
                "detail_level": "dense",
                "include_clinical_hints": True,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": True,
            },
            "ot": {
                "name_he": "מטפלת בעיסוק",
                "terminology": "clinical",
                "detail_level": "dense",
                "include_clinical_hints": True,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": True,
            },
            "speech_therapist": {
                "name_he": "קלינאית תקשורת",
                "terminology": "clinical",
                "detail_level": "dense",
                "include_clinical_hints": True,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": False,
            },
            "pediatrician": {
                "name_he": "רופא ילדים",
                "terminology": "clinical",
                "detail_level": "moderate",
                "include_clinical_hints": True,
                "include_practical_strategies": False,
                "include_strengths_first": False,
                "include_open_questions": False,
            },
            "kindergarten": {
                "name_he": "גננת",
                "terminology": "educational",
                "detail_level": "moderate",
                "include_clinical_hints": False,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": False,
            },
            "teacher": {
                "name_he": "מורה",
                "terminology": "educational",
                "detail_level": "moderate",
                "include_clinical_hints": False,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": False,
            },
            "daycare": {
                "name_he": "מטפלת במעון",
                "terminology": "warm",
                "detail_level": "light",
                "include_clinical_hints": False,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": False,
            },
            "grandparent": {
                "name_he": "סבא/סבתא",
                "terminology": "warm",
                "detail_level": "light",
                "include_clinical_hints": False,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": False,
            },
            "family": {
                "name_he": "משפחה",
                "terminology": "warm",
                "detail_level": "light",
                "include_clinical_hints": False,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": False,
            },
            "parent_peer": {
                "name_he": "הורה אחר",
                "terminology": "warm",
                "detail_level": "moderate",
                "include_clinical_hints": False,
                "include_practical_strategies": True,
                "include_strengths_first": True,
                "include_open_questions": False,
            },
        }
        return profiles.get(profile_id, profiles["family"])

    def _get_profile_instructions(self, profile: Dict, time_available: str) -> str:
        """Get specific instructions based on profile."""
        instructions = []

        if profile["terminology"] == "clinical":
            instructions.append("השתמש בטרמינולוגיה מקצועית ורלוונטית")
        elif profile["terminology"] == "warm":
            instructions.append("השתמש בשפה חמה ונגישה, בלי מונחים מקצועיים")
        else:
            instructions.append("השתמש בשפה פשוטה ומובנת")

        if time_available == "brief":
            instructions.append("כתוב סיכום קצר ותמציתי (5-7 נקודות עיקריות)")
        elif time_available == "comprehensive":
            instructions.append("כתוב סיכום מקיף ומפורט")
        else:
            instructions.append("כתוב סיכום מאוזן עם מספיק פירוט")

        if profile.get("include_strengths_first"):
            instructions.append("התחל מהחוזקות של הילד לפני האתגרים")

        return "\n".join(f"- {i}" for i in instructions)


# Singleton instance for easy access
_service_instance: Optional[ChittaService] = None


def get_chitta_service() -> ChittaService:
    """Get or create the Chitta service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChittaService()
    return _service_instance
