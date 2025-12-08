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
from .models import SynthesisReport, ConversationMemory

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

            # Stage 2: Guidelines ready (parent accepted, guidelines generated)
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

    # ========================================
    # VIDEO CONSENT & GUIDELINES
    # ========================================

    async def accept_video_suggestion(self, family_id: str, cycle_id: str) -> Dict[str, Any]:
        """
        Parent accepted video suggestion.

        NOW we generate guidelines (LLM call happens here).
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

        # Generate personalized guidelines using LLM
        scenarios = await self._generate_personalized_video_guidelines(gestalt, cycle)

        if not scenarios:
            return {"error": "Failed to generate video guidelines"}

        # Add scenarios to cycle
        cycle.video_scenarios = scenarios

        # Persist
        await self._persist_gestalt(family_id, gestalt)

        # Return parent-facing format (no hypothesis details)
        return {
            "status": "ready",
            "cycle_id": cycle_id,
            "guidelines": self._build_guidelines_response(gestalt, scenarios),
        }

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

        for scenario in pending_scenarios:
            # Analyze the video with sophisticated prompt
            analysis_result = await self._analyze_video(gestalt, cycle, scenario)

            if analysis_result:
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

        return {
            "status": "analyzed",
            "cycle_id": cycle_id,
            "insights": insights,
            "evidence_added": evidence_added,
            "strengths_found": strengths_found,
            "confidence_update": {
                "before": confidence_before,
                "after": cycle.confidence,
                "verdict": hypothesis_evidence.get("overall_verdict", "unknown"),
            } if cycle.curiosity_type == "hypothesis" else None,
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

4. **Use MM:SS Timestamps:** Every observation must include when it happened (e.g., "01:15" for 1 minute 15 seconds)

---

## Output JSON Structure

Return a valid JSON object with this structure:

```json
{{
  "hypothesis_evidence": {{
    "target_hypothesis": "{cycle.theory or cycle.focus}",
    "overall_verdict": "<supports|contradicts|mixed|inconclusive>",
    "confidence_level": "<High|Moderate|Low>",
    "reasoning": "<2-3 sentences explaining what the video tells us about the hypothesis>",
    "supporting_evidence": [
      {{
        "observation": "<Specific behavior using parent's vocabulary>",
        "timestamp": "<MM:SS>",
        "why_this_supports": "<Explain the connection>"
      }}
    ],
    "contradicting_evidence": [
      {{
        "observation": "<Specific behavior that contradicts>",
        "timestamp": "<MM:SS>",
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
      "timestamp": "<MM:SS>",
      "domain": "<social|emotional|motor|cognitive|sensory|regulation>"
    }}
  ],

  "strengths_observed": [
    {{
      "strength": "<What the child did well>",
      "timestamp": "<MM:SS>",
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
1. Use parent's vocabulary when describing behaviors
2. ALWAYS find strengths - this is NON-NEGOTIABLE
3. Use MM:SS format for all timestamps
4. The parent NEVER sees the hypothesis - insights must be warm and general
5. Contradictions are valuable - if behavior doesn't match hypothesis, that's data
6. Return ONLY valid JSON, no additional text
"""

        try:
            # Check if video file exists
            if not scenario.video_path or not os.path.exists(scenario.video_path):
                logger.warning(f"Video file not found: {scenario.video_path}")
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
            logger.info(f"📤 Uploading video to Gemini: {scenario.video_path}")
            uploaded_file = client.files.upload(file=scenario.video_path)

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
        # Extract observations for evidence
        observations = []
        for obs in result.get("observations_for_evidence", []):
            observations.append({
                "content": obs.get("content", ""),
                "effect": obs.get("effect", "supports"),
                "timestamp": obs.get("timestamp", ""),
                "domain": obs.get("domain", "general"),
            })

        # Extract parent-facing insights
        insights = result.get("parent_facing_insights", [])

        # Extract hypothesis evidence for cycle update
        hypothesis_evidence = result.get("hypothesis_evidence", {})

        # Extract strengths
        strengths = result.get("strengths_observed", [])

        return {
            "observations": observations,
            "insights": insights,
            "hypothesis_evidence": hypothesis_evidence,
            "strengths_observed": strengths,
            "holistic_summary": result.get("holistic_summary", {}),
            "focus_point_findings": result.get("focus_point_findings", []),
            "suggested_next_steps": result.get("suggested_next_steps", []),
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
                "timestamp": "00:00",
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


# Singleton instance for easy access
_service_instance: Optional[ChittaService] = None


def get_chitta_service() -> ChittaService:
    """Get or create the Chitta service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChittaService()
    return _service_instance
