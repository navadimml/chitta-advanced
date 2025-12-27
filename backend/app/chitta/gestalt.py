"""
Darshan - The Observing Intelligence

Darshan HOLDS, NOTICES, and ACTS.
Child and Session are its memory. Darshan is the mind.

THREE PUBLIC METHODS:
1. process_message(message) -> Response
2. get_active_curiosities() -> List[Curiosity]
3. synthesize() -> Optional[SynthesisReport]

CRITICAL: Two-phase LLM architecture required.
- Phase 1: Perception with tools (LLM perceives message, extracts data)
- Phase 2: Response without tools (LLM generates natural response)

Tool calls and text response CANNOT be reliably combined.
"""

import logging
import os
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union

# V2: Type-aware curiosity system (replaces old Curiosities class)
from .curiosity_types import (
    BaseCuriosity,
    Discovery,
    Question,
    Hypothesis,
    Pattern as CuriosityPattern,  # Renamed to avoid conflict with models.Pattern
    Evidence,
)
from .curiosity_manager import CuriosityManager
from .events import CuriosityEvent, Change
from .event_store import InMemoryEventStore, EventStore
from .event_recorder import EventRecorder
from .decay import DecayManager, DecayConfig
from .cascades import CascadeHandler
from .models import (
    Understanding,
    TemporalFact,
    Evidence,
    Story,
    JournalEntry,
    Pattern,
    Essence,
    ToolCall,
    PerceptionResult,
    TurnContext,
    Response,
    SynthesisReport,
    Message,
    Crystal,
    SharedSummary,
    DevelopmentalMilestone,
    ParentContext,
    VideoScenario,
    parse_temporal,
    generate_id,
    # Cognitive trace models for dashboard
    CognitiveTurn,
    ToolCallRecord,
    StateDelta,
)
from .formatting import (
    format_understanding,
    format_curiosities,
    format_perception_summary,
    format_turn_guidance,
    format_crystal,
    format_parent_context,
    format_child_gender_context,
    build_identity_section,
    build_perception_tools_description,
    build_response_language_instruction,
)
from .tools import get_perception_tools
from .clinical_gaps import ClinicalGaps, ClinicalGap

# Import LLM abstraction layer
from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message as LLMMessage, LLMResponse


logger = logging.getLogger(__name__)


class Darshan:
    """
    The observing intelligence - an expert developmental psychologist.

    Darshan HOLDS, NOTICES, and ACTS.
    Child and Session are its memory. Darshan is the mind.

    CRITICAL: Two-phase architecture required.
    - Phase 1: Perception with tools (LLM perceives message, extracts data)
    - Phase 2: Response without tools (LLM generates natural response)

    Tool calls and text response CANNOT be reliably combined.
    """

    def __init__(
        self,
        child_id: str,
        child_name: Optional[str],
        understanding: Understanding,
        stories: List[Story],
        journal: List[JournalEntry],
        session_history: List[Message],
        crystal: Optional[Crystal] = None,
        shared_summaries: Optional[List[SharedSummary]] = None,
        child_birth_date: Optional["date"] = None,
        child_gender: Optional[str] = None,
        parent_context: Optional[ParentContext] = None,
        cognitive_turns: Optional[List[CognitiveTurn]] = None,
        curiosity_manager: Optional[CuriosityManager] = None,
        event_store: Optional[EventStore] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize Darshan.

        Args:
            child_id: Unique identifier for the child
            child_name: Child's name (if known)
            understanding: Current understanding of the child
            stories: Captured stories
            journal: Journal entries
            session_history: Recent conversation history
            crystal: Cached synthesis (patterns, essence, pathways)
            shared_summaries: Previously generated Letters for sharing
            child_birth_date: Child's birth date for age-based temporal calculations
            child_gender: Child's gender for correct pronoun usage (male/female/unknown)
            parent_context: Parent context for gender-appropriate verb forms
            cognitive_turns: Cognitive traces for dashboard (optional, persisted separately)
            curiosity_manager: Type-aware curiosity manager
            event_store: Event store for event sourcing
            session_id: Current session ID for event recording
        """
        self.child_id = child_id
        self.child_name = child_name
        self.understanding = understanding
        self.stories = stories
        self.journal = journal
        self.session_history = session_history
        self.crystal = crystal
        self.shared_summaries = shared_summaries or []
        self.child_birth_date = child_birth_date
        self.child_gender = child_gender
        self.parent_context = parent_context

        # Cognitive traces for dashboard (not persisted with darshan - separate table)
        self.cognitive_turns: List[CognitiveTurn] = cognitive_turns or []

        # Session-level flags (persisted to survive page reload)
        # Used for guided collection mode and other temporary states
        self.session_flags: Dict[str, Any] = {}

        # Topic switch detection - track domains from previous turn
        self._last_turn_domains: List[str] = []

        # Lazy-loaded LLM providers
        self._llm = None
        self._strong_llm = None

        # Type-aware curiosity system
        self._session_id = session_id or generate_id()
        self._curiosity_manager = curiosity_manager or CuriosityManager()
        self._event_store = event_store or InMemoryEventStore()
        self._event_recorder = EventRecorder(
            event_store=self._event_store,
            session_id=self._session_id,
            child_id=child_id,
        )
        self._decay_manager = DecayManager()
        self._cascade_handler = CascadeHandler(self._curiosity_manager)

    @property
    def _curiosities(self) -> CuriosityManager:
        """Alias for _curiosity_manager for backwards compatibility."""
        return self._curiosity_manager

    def _get_llm(self):
        """Get LLM provider for conversation (Phase 1 & 2)."""
        if self._llm is None:
            model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
            provider = os.getenv("LLM_PROVIDER", "gemini")
            self._llm = create_llm_provider(
                provider_type=provider,
                model=model,
                use_enhanced=True,
            )
        return self._llm

    def _get_strong_llm(self):
        """Get strong LLM for synthesis and pattern detection."""
        if self._strong_llm is None:
            model = os.getenv("STRONG_LLM_MODEL", "gemini-2.5-pro")
            provider = os.getenv("LLM_PROVIDER", "gemini")
            self._strong_llm = create_llm_provider(
                provider_type=provider,
                model=model,
                use_enhanced=True,
            )
        return self._strong_llm

    # ========================================
    # PHASE 0: Decay (Mechanical)
    # ========================================

    def _apply_decay_and_check_dormancy(self) -> None:
        """
        Apply time-based pull decay and transition dormant curiosities.

        This is PHASE 0 - happens before perception, purely mechanical.
        - Pull decays exponentially based on time since last update
        - Curiosities with low pull + long inactivity become dormant
        - Events are recorded for provenance

        Only PULL decays - fullness/confidence represent understanding
        and persist until explicitly changed via evidence/update.
        """
        now = datetime.now()

        # Apply decay to all curiosities
        all_curiosities = self._curiosity_manager.get_all()
        decay_results = self._decay_manager.apply_decay_batch(all_curiosities, now=now)

        # Log significant decay
        for curiosity_id, decay_amount in decay_results:
            if decay_amount > 0.01:  # Only log meaningful decay
                logger.debug(f"Decay applied to {curiosity_id}: -{decay_amount:.3f} pull")

        # Check for dormancy candidates
        dormancy_candidates = self._decay_manager.find_dormancy_candidates(
            all_curiosities, now=now
        )

        for curiosity in dormancy_candidates:
            old_status = curiosity.status
            curiosity.status = "dormant"
            curiosity.last_updated = now
            curiosity.last_updated_reasoning = (
                f"Dormancy: pull={curiosity.pull:.2f}, inactive beyond threshold"
            )

            # Log dormancy transition (event recording is async, handled elsewhere)
            logger.info(f"Curiosity '{curiosity.focus}' transitioned to dormant (pull={curiosity.pull:.2f})")

    def _extract_domains_from_tool_calls(self, tool_calls: List[ToolCall]) -> List[str]:
        """Extract domains touched in this turn from tool calls."""
        domains = set()
        for tc in tool_calls:
            if tc.name in ("notice", "wonder", "capture_story"):
                domain = tc.args.get("domain")
                if domain:
                    domains.add(domain)
                # capture_story may have domains list
                if tc.name == "capture_story":
                    for d in tc.args.get("domains", []):
                        domains.add(d)
        return list(domains)

    def _detect_topic_shift(self, new_domains: List[str]) -> bool:
        """Detect if parent shifted to a new topic area."""
        if not self._last_turn_domains or not new_domains:
            return False
        overlap = set(new_domains) & set(self._last_turn_domains)
        # Shift if no overlap and new domains exist
        return len(overlap) == 0

    def _apply_topic_shift_decay(self, new_domains: List[str]) -> None:
        """
        Apply extra decay to curiosities not matching the new topic.

        When parent shifts topic, curiosities about the old topic become
        less immediately relevant. This doesn't mean they're unimportant -
        just that the conversation's focus has moved.
        """
        if not new_domains:
            return

        active_curiosities = self._curiosity_manager.get_active()
        for curiosity in active_curiosities:
            curiosity_domain = getattr(curiosity, "domain", "general")
            if curiosity_domain not in new_domains and curiosity_domain != "general":
                old_pull = curiosity.pull
                # Apply 30% extra decay for off-topic curiosities
                curiosity.pull = max(0.1, curiosity.pull * 0.7)
                if old_pull - curiosity.pull > 0.01:
                    logger.debug(
                        f"Topic shift decay: {curiosity.focus[:30]}... "
                        f"({curiosity_domain} not in {new_domains}): "
                        f"{old_pull:.2f} → {curiosity.pull:.2f}"
                    )

    # ========================================
    # THREE PUBLIC METHODS - The Surface
    # ========================================

    async def process_message(
        self,
        message: str,
        parent_role: Optional[str] = None,
    ) -> Response:
        """
        Process a parent message with TWO-PHASE architecture.

        Phase 0: Decay (mechanical)
          - Apply time-based pull decay to all curiosities
          - Transition dormant curiosities

        Phase 1: Perception (with tools)
          - LLM perceives intent, context, significance
          - LLM extracts data via tool calls
          - Returns: tool calls only

        Phase 2: Response Generation (without tools)
          - LLM has perception context
          - LLM generates natural Hebrew response
          - Returns: text only

        Also creates a CognitiveTurn for dashboard review.
        """
        # PHASE 0: Apply decay before anything else
        self._apply_decay_and_check_dormancy()

        # Calculate turn number
        turn_number = len(self.cognitive_turns) + 1

        # Create cognitive turn to track this interaction
        cognitive_turn = CognitiveTurn.create(
            child_id=self.child_id,
            turn_number=turn_number,
            parent_message=message,
            parent_role=parent_role,
        )

        # Build context for this turn
        turn_context = self._build_turn_context(message)

        # PHASE 1: Perception with tools
        perception_result = await self._phase1_perceive(turn_context)

        # Record tool calls in cognitive turn
        cognitive_turn.tool_calls = [
            ToolCallRecord(
                tool_name=tc.name,
                arguments=tc.args,
            )
            for tc in perception_result.tool_calls
        ]
        cognitive_turn.perceived_intent = perception_result.perceived_intent

        # Apply learnings from tool calls (returns StateDelta)
        state_delta = self._apply_learnings(perception_result.tool_calls)
        cognitive_turn.state_delta = state_delta

        # Topic shift detection - decay off-topic curiosities
        new_domains = self._extract_domains_from_tool_calls(perception_result.tool_calls)
        if self._detect_topic_shift(new_domains):
            logger.info(f"📍 Topic shift detected: {self._last_turn_domains} → {new_domains}")
            self._apply_topic_shift_decay(new_domains)
        # Update last turn domains for next turn
        if new_domains:
            self._last_turn_domains = new_domains

        # PHASE 2: Response without tools
        response_text = await self._phase2_respond(turn_context, perception_result)

        # Record response in cognitive turn
        cognitive_turn.response_text = response_text
        cognitive_turn.active_curiosities = [
            c.focus for c in self.get_active_curiosities()[:5]  # Top 5 active
        ]

        # Store cognitive turn
        self.cognitive_turns.append(cognitive_turn)

        # Update session history
        self.session_history.append(Message(role="user", content=message))
        self.session_history.append(Message(role="assistant", content=response_text))

        # Keep history manageable (last 20 messages)
        if len(self.session_history) > 20:
            self.session_history = self.session_history[-20:]

        # Determine if crystallization should be triggered
        should_crystallize = self._should_trigger_crystallization(perception_result.tool_calls)

        return Response(
            text=response_text,
            curiosities=self.get_active_curiosities(),
            open_questions=self._curiosity_manager.get_gaps(),
            should_crystallize=should_crystallize,
        )

    def _should_trigger_crystallization(self, tool_calls: List[ToolCall]) -> bool:
        """
        Determine if this turn's learnings warrant background crystallization.

        Important moments that trigger crystallization:
        - Story captured (stories are GOLD)
        - Hypothesis created or spawned exploration
        - Significant evidence added
        - Early conversation: First crystal after ~5 observations (for holistic context)

        We don't crystallize on every turn - only on meaningful learning.
        """
        # Early conversation: trigger first synthesis after enough observations
        # This ensures early turns have some holistic context
        if self.crystal is None:
            observation_count = len(self.understanding.observations)
            if observation_count >= 5:
                logger.info(f"🌟 Early synthesis trigger: {observation_count} observations, no crystal yet")
                return True

        if not tool_calls:
            return False

        important_tools = {"capture_story"}
        has_important = any(tc.name in important_tools for tc in tool_calls)

        # Check for hypothesis creation via wonder
        has_hypothesis = any(
            tc.name == "wonder" and tc.args.get("type") == "hypothesis"
            for tc in tool_calls
        )

        # Check for significant evidence (supports or contradicts)
        has_significant_evidence = any(
            tc.name == "add_evidence" and tc.args.get("effect") in ("supports", "contradicts")
            for tc in tool_calls
        )

        return has_important or has_hypothesis or has_significant_evidence

    def get_active_curiosities(self) -> List[BaseCuriosity]:
        """What am I curious about right now?"""
        return self._curiosity_manager.get_active()

    def get_latest_cognitive_turn(self) -> Optional[CognitiveTurn]:
        """Get the most recent cognitive turn for persistence."""
        if self.cognitive_turns:
            return self.cognitive_turns[-1]
        return None

    def get_cognitive_turns(self) -> List[CognitiveTurn]:
        """Get all cognitive turns for this session."""
        return self.cognitive_turns

    def synthesize(self) -> Optional[SynthesisReport]:
        """
        Create synthesis when conditions are ripe.
        Pattern detection happens HERE with STRONGEST model.
        Called on demand, not every turn.
        """
        if not self._should_synthesize():
            return None
        return self._create_synthesis_report()

    # ========================================
    # TWO-PHASE ARCHITECTURE
    # ========================================

    async def _phase1_perceive(self, context: TurnContext) -> PerceptionResult:
        """
        Phase 1: Perception with tools.

        Darshan perceives the message and extracts data.
        Intent detection, story analysis, significance assessment
        all happen INSIDE the LLM - not with keyword matching.

        Configuration:
        - temperature=0.0 (reliable perception)
        - functions=tools (enables function calling)
        """
        system_prompt = self._build_perception_prompt(context)
        tools = get_perception_tools()

        # Build messages for LLM
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=context.this_message),
        ]

        try:
            llm = self._get_llm()
            llm_response: LLMResponse = await llm.chat(
                messages=messages,
                functions=tools,  # Enable function calling
                temperature=0.0,  # Low temp for reliable perception
                max_tokens=2000,
            )

            # Convert function calls to our ToolCall model
            tool_calls = [
                ToolCall(name=fc.name, args=fc.arguments)
                for fc in llm_response.function_calls
            ]

            return PerceptionResult(
                tool_calls=tool_calls,
                perceived_intent=self._infer_intent_from_calls(tool_calls),
            )

        except Exception as e:
            logger.error(f"Phase 1 perception error: {e}")
            return PerceptionResult(tool_calls=[], perceived_intent="conversational")

    async def _phase2_respond(self, context: TurnContext, perception: PerceptionResult) -> str:
        """
        Phase 2: Response without tools.

        The LLM generates a natural Hebrew response.
        Has full context including what was just perceived.

        Configuration:
        - temperature=0.7 (natural conversation)
        - functions=None (forces text response)
        """
        system_prompt = self._build_response_prompt(context, perception)

        # Build messages with history
        messages = [LLMMessage(role="system", content=system_prompt)]

        # Add conversation history
        for msg in context.recent_history[-10:]:
            messages.append(LLMMessage(role=msg["role"], content=msg["content"]))

        # Add current message
        messages.append(LLMMessage(role="user", content=context.this_message))

        try:
            llm = self._get_llm()
            llm_response: LLMResponse = await llm.chat(
                messages=messages,
                functions=None,  # NO TOOLS - forces text response
                temperature=0.7,
                max_tokens=4000,
            )

            response_text = llm_response.content or "אני מתקשה להגיב כרגע. אפשר לנסות שוב?"

            # Strip any <thoughts>...</thoughts> tags that leaked through
            # The LLM sometimes includes internal reasoning that shouldn't be shown
            response_text = re.sub(r'<thoughts>.*?</thoughts>\s*', '', response_text, flags=re.DOTALL)
            response_text = response_text.strip()

            return response_text or "אני מתקשה להגיב כרגע. אפשר לנסות שוב?"

        except Exception as e:
            logger.error(f"Phase 2 response error: {e}")
            return "אני מתקשה להגיב כרגע. אפשר לנסות שוב?"

    # ========================================
    # PROMPT BUILDING
    # ========================================

    def _build_turn_context(self, message: str) -> TurnContext:
        """Build context for this turn."""
        return TurnContext(
            understanding=self.understanding,
            curiosities=self.get_active_curiosities()[:5],
            recent_history=[msg.to_dict() for msg in self.session_history[-10:]],
            this_message=message,
        )

    def _build_perception_prompt(self, context: TurnContext) -> str:
        """
        Build prompt for Phase 1 (perception).

        Darshan is asked to:
        1. Perceive what the parent is sharing (intent emerges from understanding)
        2. Extract relevant data via tool calls
        3. Assess significance if a story is shared

        This is where intent detection ACTUALLY happens - by LLM understanding,
        not keyword matching.
        """
        child_name = self.child_name or "THIS CHILD"

        # Include Crystal if available - provides holistic understanding
        crystal_section = ""
        if self.crystal:
            crystal_section = f"""
## HOLISTIC UNDERSTANDING (Crystal)

{format_crystal(self.crystal)}
"""

        # Check for guided collection mode - add extraction hints
        guided_extraction_section = ""
        if self.session_flags.get("preparing_summary_for"):
            gaps = self.session_flags.get("guided_collection_gaps", [])
            if gaps:
                gap_hints = []
                for g in gaps[:3]:
                    field = g.get("field", "") if isinstance(g, dict) else getattr(g, "field", "")
                    if field == "birth_history":
                        gap_hints.append("birth/pregnancy info → record_milestone(domain='birth_history', milestone_type='birth' for birth moment, 'concern' for pregnancy events)")
                    elif field == "milestones":
                        gap_hints.append("milestone timing (first words, walking, etc.) → record_milestone(domain=..., milestone_type='achievement')")
                    elif field == "family_developmental_history":
                        gap_hints.append("family history → notice(domain='context')")
                    elif field == "sleep":
                        gap_hints.append("sleep info → notice(domain='sleep')")
                    elif field == "regression":
                        gap_hints.append("regression/lost skills → IF YES: record_milestone(milestone_type='regression'), IF NO: notice('אין נסיגה התפתחותית', domain='regression')")
                    elif field == "sensory_patterns":
                        gap_hints.append("sensory info → notice(domain='sensory')")
                if gap_hints:
                    guided_extraction_section = f"""
## CRITICAL: EXTRACTION PRIORITY

**Record any info about:**
{chr(10).join(f'- {h}' for h in gap_hints)}

**IMPORTANT: Record NEGATIVE answers too!**
When parent says "לא", "אין", "לא היה" - this is ALSO valuable information to record:
- "לא הייתה נסיגה" → notice("אין נסיגה התפתחותית מדווחת - לא איבדה כישורים", domain="regression")
- "ישן טוב" / "אין בעיות שינה" → notice("שינה תקינה לפי דיווח ההורה", domain="sleep")
- "התפתחות רגילה" → notice("התפתחות תקינה לפי דיווח ההורה", domain="milestones")

**Use the correct tool - notice() for general observations, record_milestone() for developmental events with timing!**
"""

        # Parent gender context for appropriate verb forms
        parent_context_section = format_parent_context(self.parent_context)

        # Child gender context for appropriate pronouns
        child_gender_section = format_child_gender_context(self.child_gender, self.child_name)

        # Find solid patterns that haven't spawned questions yet
        solid_patterns_section = ""
        patterns_needing_questions = [
            p for p in self._curiosity_manager.get_patterns()
            if p.status == "solid" and len(p.spawned_questions) == 0
        ]
        if patterns_needing_questions:
            pattern_lines = [
                f"- **{p.focus}**: {p.insight}" for p in patterns_needing_questions[:3]
            ]
            solid_patterns_section = f"""
## SOLID PATTERNS READY FOR DEEPER EXPLORATION

These patterns are well-established but haven't generated follow-up questions yet.
Consider using wonder(type='question') to explore their implications:

{chr(10).join(pattern_lines)}
"""

        return f"""
# CHITTA - Perception Phase

You are Chitta, an expert developmental psychologist (0.5-18 years).
You are perceiving what a parent shared and extracting relevant information.
{parent_context_section}{child_gender_section}{crystal_section}{guided_extraction_section}
## WHAT I KNOW ABOUT {child_name}

{format_understanding(context.understanding)}

## WHAT I'M CURIOUS ABOUT

{format_curiosities(context.curiosities)}
{solid_patterns_section}
## YOUR TASK

Read the parent's message and extract what's relevant:

1. **Perceive the message type** - Is this a story? A question? Emotional expression?
   (You understand this from reading - no keywords needed)

2. **If it's a story** - Use capture_story to record what it reveals.
   Stories are GOLD. A skilled observer sees MULTIPLE signals in ONE story.

3. **If you learn something** - Use notice to record observations.

4. **If something sparks curiosity** - Use wonder to spawn exploration.

5. **If evidence relates to active exploration** - Use add_evidence.

{build_perception_tools_description()}
"""

    def _build_response_prompt(self, context: TurnContext, perception: PerceptionResult) -> str:
        """
        Build prompt for Phase 2 (response).

        Turn-specific guidance is computed based on what was perceived.
        Crystal provides holistic context for more insightful responses.
        Guided collection mode injects gap context for Letter preparation.
        """
        child_name = self.child_name or "THIS CHILD"

        # Include Crystal if available - provides holistic understanding
        crystal_section = ""
        if self.crystal:
            crystal_section = f"""
## HOLISTIC UNDERSTANDING (Crystal)

{format_crystal(self.crystal)}
"""

        # Check for guided collection mode
        # IMPORTANT: Re-check gaps on EVERY message using actual data
        # This ensures we always show only CURRENTLY missing gaps
        guided_collection_section = ""
        if self.session_flags.get("preparing_summary_for"):
            recipient_type = self.session_flags["preparing_summary_for"]

            # Re-run readiness check to get CURRENT missing gaps (not stale stored ones)
            clinical_gaps_checker = ClinicalGaps()
            current_readiness = clinical_gaps_checker.check_readiness(
                recipient_type=recipient_type,
                understanding=self.understanding,
                child=None,
                child_birth_date=self.child_birth_date,  # Pass birth date from Darshan
            )

            # Get currently missing gaps
            current_gaps = current_readiness.missing_critical + current_readiness.missing_important

            # Update session_flags with fresh gaps
            self.session_flags["guided_collection_gaps"] = [
                {"field": g.field, "description": g.parent_description, "question": g.parent_question}
                for g in current_gaps
            ]

            if current_gaps:
                guided_collection_section = clinical_gaps_checker.get_collection_context(
                    recipient_type, current_gaps
                )
            else:
                # All gaps filled! Offer graceful exit with user choice
                logger.info(f"All guided collection gaps filled for {self.child_id}, offering graceful exit")

                # Don't clear flags yet - let parent confirm they're ready
                # Flags will be cleared when they create the summary in ChildSpace

                guided_collection_section = f"""
## GUIDED COLLECTION COMPLETE - OFFER CHOICE

All the information needed for the {recipient_type} summary has been collected.

**OFFER THE PARENT A CHOICE (don't just switch):**

Option 1: Create summary now
"יש לי מספיק מידע ליצור את הסיכום ל{recipient_type}. רוצה שתלכי לחלל הילד ליצור אותו עכשיו?"

Option 2: Check if they want to add anything
"לפני שאני מסיימת לאסוף - יש משהו נוסף שחשוב לך שאדע לקראת הפגישה?"

**YOUR RESPONSE MUST:**
1. Warmly acknowledge completion: "מעולה! יש לי את כל מה שצריך"
2. **ASK** if they want to add anything or create the summary now
3. Let THEM decide the next step

**EXAMPLE RESPONSE:**
"מעולה, יש לי מספיק מידע לסיכום.
לפני שתלכי ליצור אותו בחלל הילד - יש משהו נוסף שחשוב לך להוסיף?"

**DO NOT:**
- Immediately pivot to a new topic without asking
- Assume they're done without checking
- End with a closed statement
"""

        # Compute guidance from perception
        captured_story = any(tc.name == "capture_story" for tc in perception.tool_calls)
        spawned_curiosity = any(tc.name == "wonder" for tc in perception.tool_calls)
        added_evidence = any(tc.name == "add_evidence" for tc in perception.tool_calls)

        # Extract response type if LLM classified it (no string matching!)
        response_type = None
        for tc in perception.tool_calls:
            if tc.name == "classify_response":
                response_type = tc.args.get("response_type")
                break

        # Detect general clinical gaps for soft guidance
        # These are NOT agenda items - just hints for natural weaving
        clinical_gaps = []
        if not self.session_flags.get("preparing_summary_for"):
            # Only add gap hints when NOT in guided collection mode
            # (Guided collection has its own explicit gap prompts)
            clinical_gaps_checker = ClinicalGaps()
            # Check gaps that would be universally useful (pediatrician as baseline)
            readiness = clinical_gaps_checker.check_readiness(
                "pediatrician",
                self.understanding,
            )
            # Combine critical and important gaps
            all_gaps = readiness.missing_critical + readiness.missing_important
            if all_gaps:
                clinical_gaps = all_gaps[:5]  # Limit to top 5

        # Get top-pull curiosity for urgency awareness
        top_curiosity_pull = None
        top_curiosity_focus = None
        active_curiosities = self._curiosity_manager.get_active()
        if active_curiosities:
            sorted_by_pull = sorted(active_curiosities, key=lambda c: c.pull, reverse=True)
            if sorted_by_pull:
                top = sorted_by_pull[0]
                top_curiosity_pull = top.pull
                top_curiosity_focus = top.focus

        guidance = format_turn_guidance(
            captured_story=captured_story,
            spawned_curiosity=spawned_curiosity,
            added_evidence=added_evidence,
            perceived_intent=perception.perceived_intent,
            clinical_gaps=clinical_gaps,
            top_curiosity_pull=top_curiosity_pull,
            top_curiosity_focus=top_curiosity_focus,
            response_type=response_type,
        )

        # Parent gender context for appropriate verb forms
        parent_context_section = format_parent_context(self.parent_context)

        # Child gender context for appropriate pronouns
        child_gender_section = format_child_gender_context(self.child_gender, self.child_name)

        return f"""
# CHITTA - Response Phase

You are Chitta, an expert developmental psychologist (0.5-18 years).
You are responding to what the parent shared.

{build_identity_section()}
{parent_context_section}{child_gender_section}{crystal_section}
{guided_collection_section}
## WHAT I KNOW ABOUT {child_name}

{format_understanding(context.understanding)}

## WHAT WE JUST PERCEIVED

{format_perception_summary(perception)}

{guidance}

{build_response_language_instruction()}

## PRINCIPLES

- Curiosity drives exploration, not checklists
- Stories are GOLD - honor what was shared
- One question at a time, if any
- Follow the flow, don't force agenda
- Use the holistic understanding (Crystal) to connect what's shared to patterns
- **EXCEPTION**: If CONTEXT: PREPARING A SUMMARY section exists above, you ARE following an agenda - cover all listed items before ending

## COMMUNICATION STYLE - CRITICAL

**INTERNAL MECHANISM - NEVER SHARE:**
Your curiosity, wondering, exploration, and hypothesis mechanisms are INTERNAL.
NEVER say things like:
- "זה מעורר אצלי סקרנות לגבי..."
- "אני תוהה/תוהה אם..."
- "זה מעלה שתי שאלות..."
- "הבחירה שלה מעוררת אצלי..."

Instead, ask questions naturally without explaining WHY you're curious.

**EMPATHY - SHOW, DON'T TELL:**
NEVER use explicit empathy statements like:
- "אני שומע/ת אותך"
- "אני מבינ/ה"
- "נשמע קשה"
- "אני כאן בשבילך"

The parent should FEEL heard through your response, not be TOLD they're heard.
Show empathy by:
- Engaging thoughtfully with what they shared
- Asking relevant follow-up questions
- Reflecting understanding through the content of your response

**GOOD EXAMPLE:**
Parent: "היא מסתגרת בחדר ולא יוצאת"
Response: "הקריאה יכולה להיות דרך נפלאה להכיר עולמות חדשים. איך נראית היציאה שלה מהחדר כשיש משהו שמעניין אותה?"

**BAD EXAMPLE:**
Response: "אני שומע אותך. זה מעורר אצלי סקרנות לגבי שני דברים..."

RESPOND IN NATURAL HEBREW. Be warm, professional, insightful.
"""

    def _infer_intent_from_calls(self, tool_calls: List[ToolCall]) -> str:
        """
        Infer message intent from what tools were called.

        If capture_story was called → story
        If no extraction tools called but message has '?' → likely question
        This is a HEURISTIC for guidance, not the source of truth.
        """
        if any(tc.name == "capture_story" for tc in tool_calls):
            return "story"
        if any(tc.name == "notice" for tc in tool_calls):
            return "informational"
        if any(tc.name == "wonder" for tc in tool_calls):
            return "exploratory"
        return "conversational"

    # ========================================
    # TOOL CALL HANDLERS
    # ========================================

    def _apply_learnings(self, tool_calls: List[ToolCall]) -> StateDelta:
        """
        Apply what LLM learned to child state.

        Returns a StateDelta capturing all changes made.
        """
        # Debug: Log what tool calls we received from Phase 1
        logger.info(f"📊 Phase 1 returned {len(tool_calls)} tool calls")
        for call in tool_calls:
            logger.info(f"  🔧 Tool: {call.name}, args: {call.args}")

        # Track state changes for cognitive trace
        state_delta = StateDelta()

        for call in tool_calls:
            try:
                if call.name == "notice":
                    self._handle_notice(call.args)
                    # Track observation added
                    state_delta.observations_added.append(call.args.get("observation", ""))
                elif call.name == "wonder":
                    self._handle_wonder(call.args)
                    # Track curiosity spawned
                    state_delta.curiosities_spawned.append(call.args.get("about", ""))
                elif call.name == "capture_story":
                    self._handle_capture_story(call.args)
                    # Stories spawn observations internally, tracked separately
                elif call.name == "add_evidence":
                    self._handle_add_evidence(call.args)
                    # Track evidence added
                    state_delta.evidence_added.append({
                        "curiosity_focus": call.args.get("cycle_id", ""),  # investigation_id in args
                        "content": call.args.get("evidence", ""),
                        "effect": call.args.get("effect", "supports"),
                    })
                # spawn_exploration removed - investigations auto-start in _handle_wonder
                elif call.name == "record_milestone":
                    self._handle_record_milestone(call.args)
                elif call.name == "set_child_identity":
                    self._handle_set_child_identity(call.args)
                    # Track identity changes
                    state_delta.child_identity_set = {
                        k: v for k, v in call.args.items() if v is not None
                    }
                # V2: New tools
                elif call.name == "see_pattern":
                    self._handle_see_pattern(call.args)
                    # Track pattern emergence
                    state_delta.curiosities_spawned.append(f"pattern: {call.args.get('pattern', '')}")
                elif call.name == "update_curiosity":
                    self._handle_update_curiosity(call.args)
                    # Track curiosity update
                    state_delta.curiosities_updated.append({
                        "focus": call.args.get("focus", ""),
                        "field": "status/value",
                        "old": None,
                        "new": call.args.get("new_status") or call.args.get("new_fullness_or_confidence"),
                    })
                elif call.name == "classify_response":
                    # Just log - the classification will be used in turn guidance
                    response_type = call.args.get("response_type", "substantive")
                    reasoning = call.args.get("reasoning", "")
                    logger.info(f"📋 Response classified as: {response_type} ({reasoning})")
                    state_delta.response_type = response_type
            except Exception as e:
                logger.error(f"Error handling tool call {call.name}: {e}")

        return state_delta

    def _handle_notice(self, args: Dict[str, Any]):
        """Notice an observation about the child."""
        observation = TemporalFact(
            content=args["observation"],
            domain=args.get("domain", "general"),
            source="conversation",
            t_valid=parse_temporal(
                when_type=args.get("when_type"),
                when_value=args.get("when_value"),
                reference_time=datetime.now(),
                child_birth_date=self.child_birth_date,
            ),
            t_created=datetime.now(),
            confidence=args.get("confidence", 0.7),
        )
        self.understanding.add_observation(observation)
        self._curiosity_manager.on_observation_learned(observation)

    def _handle_wonder(self, args: Dict[str, Any]):
        """
        Spawn a new curiosity with provenance tracking.

        Tool fields:
        - focus (or "about" for compatibility)
        - fullness_or_confidence (or "certainty" for compatibility)
        - assessment_reasoning (REQUIRED)
        - evidence_refs
        - emerges_from, source_hypotheses (lineage)
        - initial_pull: Override default pull urgency (0-1)
        """
        # Support both old ("about") and new ("focus") field names
        focus = args.get("focus", args.get("about", ""))
        curiosity_type = args.get("type", "question")

        # Get provenance fields
        reasoning = args.get("assessment_reasoning", "Spawned during conversation")
        value = args.get("fullness_or_confidence", args.get("certainty", 0.3))
        emerges_from = args.get("emerges_from")
        initial_pull = args.get("initial_pull")  # May be None, meaning use type default

        if curiosity_type == "hypothesis":
            curiosity = Hypothesis.create(
                focus=focus,
                domain=args.get("domain", "general"),
                confidence=value,
                reasoning=reasoning,
                theory=args.get("theory", focus),
                video_appropriate=args.get("video_appropriate", True),
                video_value=args.get("video_value"),
                source_question=emerges_from,
            )
            if initial_pull is not None:
                curiosity.pull = initial_pull
            self._curiosity_manager.add(curiosity)

        elif curiosity_type == "question":
            curiosity = Question.create(
                focus=focus,
                domain=args.get("domain", "general"),
                fullness=value,
                reasoning=reasoning,
                question=args.get("question", focus),
                source_discovery=emerges_from,
            )
            if initial_pull is not None:
                curiosity.pull = initial_pull
            self._curiosity_manager.add(curiosity)

            # Track if this question spawned from a pattern
            if emerges_from:
                source = self._curiosity_manager.get_by_focus(emerges_from)
                if source and isinstance(source, CuriosityPattern):
                    source.spawn_question(curiosity.id, reasoning)
                    logger.info(f"🌱 Pattern spawned question: {emerges_from} → {focus}")

        elif curiosity_type == "pattern":
            curiosity = CuriosityPattern.create(
                focus=focus,
                insight=args.get("insight", focus),  # Default insight to focus if not provided
                domains_involved=args.get("domains_involved", []),
                source_hypotheses=args.get("source_hypotheses", []),
                reasoning=reasoning,
                confidence=value,
            )
            if initial_pull is not None:
                curiosity.pull = initial_pull
            self._curiosity_manager.add(curiosity)

        else:  # discovery
            curiosity = Discovery.create(
                focus=focus,
                domain=args.get("domain", "essence"),
                fullness=value,
                reasoning=reasoning,
            )
            if initial_pull is not None:
                curiosity.pull = initial_pull
            self._curiosity_manager.add(curiosity)

        pull_info = f", pull={initial_pull}" if initial_pull is not None else ""
        logger.info(f"✨ Spawned {curiosity_type}: {focus}{pull_info} (reasoning: {reasoning[:50]}...)")

    def _handle_capture_story(self, args: Dict[str, Any]):
        """Capture a story and its developmental signals."""
        story = Story.create(
            summary=args["summary"],
            reveals=args.get("reveals", []),
            domains=args.get("domains", []),
            significance=args.get("significance", 0.5),
        )
        self.stories.append(story)

        # Touch domains in curiosities
        for domain in story.domains:
            self._curiosity_manager.on_domain_touched(domain)

        # Cross-domain stories are GOLD for pattern detection
        # Spawn pattern curiosity when story reveals connections across 2+ domains
        if len(story.domains) >= 2 and story.significance >= 0.5:
            # Check if we already have a pattern curiosity for these domains
            existing_pattern = self._curiosity_manager.find_by_domains(story.domains)
            if not existing_pattern:
                # Create a pattern curiosity connecting these domains
                pattern_focus = f"קשר בין {' ל'.join(story.domains[:3])}"
                pattern_curiosity = CuriosityPattern.create(
                    focus=pattern_focus,
                    insight=f"סיפור חושף קשר בין {' ו'.join(story.domains[:3])}",
                    domains_involved=story.domains,
                    source_hypotheses=[],  # Story-spawned patterns don't start with source hypotheses
                    reasoning="Story revealed cross-domain connections",
                    confidence=0.3,  # Start tentative
                )
                pattern_curiosity.pull = 0.5 + (story.significance * 0.3)  # Higher pull for significant stories
                self._curiosity_manager.add(pattern_curiosity)
                logger.info(f"Story spawned pattern curiosity: {pattern_focus}")

        # Add journal entry
        entry = JournalEntry.create(
            summary=story.summary,
            learned=story.reveals,
            significance="notable" if story.significance > 0.7 else "routine",
            entry_type="story_captured",
        )
        self.journal.append(entry)

    def _handle_add_evidence(self, args: Dict[str, Any]):
        """
        Add evidence to an active curiosity with provenance tracking.

        Tool fields:
        - curiosity_focus (or "cycle_id" for compatibility)
        - evidence: The evidence content
        - effect: supports/contradicts/transforms
        - new_confidence: LLM's assessment of new confidence
        - effect_reasoning (REQUIRED)
        - source_observation (REQUIRED)
        """
        # Support both old ("cycle_id") and new ("curiosity_focus") field names
        curiosity_focus = args.get("curiosity_focus", args.get("cycle_id", ""))
        if not curiosity_focus:
            return

        # Get all provenance fields
        evidence_content = args.get("evidence", "")
        reasoning = args.get("effect_reasoning", "Evidence from conversation")
        effect = args.get("effect", "supports")
        new_confidence = args.get("new_confidence")
        source_observation = args.get("source_observation", "")

        # Find curiosity and update
        curiosity = self._curiosity_manager.get_by_focus(curiosity_focus)
        if curiosity and isinstance(curiosity, Hypothesis):
            old_confidence = curiosity.confidence
            old_status = curiosity.status

            # Calculate new confidence if not provided
            if new_confidence is None:
                # Use effect to adjust confidence
                if effect == "supports":
                    new_confidence = min(1.0, old_confidence + 0.1)
                elif effect == "contradicts":
                    new_confidence = max(0.0, old_confidence - 0.15)
                else:  # transforms
                    new_confidence = old_confidence  # Transforms don't change confidence

            # Create Evidence object with full provenance
            evidence = Evidence.create(
                content=evidence_content,
                effect=effect,
                session_id=self._session_id,
                source_observation=source_observation,
                reasoning=reasoning,
                confidence_before=old_confidence,
                confidence_after=new_confidence,
            )

            # Use add_evidence method - this triggers auto-status transitions!
            curiosity.add_evidence(evidence, reasoning)

            # Record event
            changes = [{"field": "confidence", "old": old_confidence, "new": curiosity.confidence}]
            if old_status != curiosity.status:
                changes.append({"field": "status", "old": old_status, "new": curiosity.status})
                logger.info(f"🔄 Hypothesis status auto-transitioned: {old_status} → {curiosity.status}")

                # Trigger cascades on status change
                if curiosity.status == "confirmed":
                    cascade_result = self._cascade_handler.handle_confirmation(
                        hypothesis=curiosity,
                        session_id=self._session_id,
                        child_id=self.child_id,
                        confirmation_reasoning=reasoning,
                    )
                    if cascade_result.crystal_needs_regeneration:
                        logger.info(f"🔄 Hypothesis confirmation triggered crystal regeneration need")
                elif curiosity.status == "refuted":
                    cascade_result = self._cascade_handler.handle_refutation(
                        hypothesis=curiosity,
                        session_id=self._session_id,
                        child_id=self.child_id,
                        refutation_reasoning=reasoning,
                    )
                    if cascade_result.crystal_needs_regeneration:
                        logger.info(f"🔄 Hypothesis refutation triggered crystal regeneration need")

            # Log changes (async event recording handled by service layer)
            logger.info(
                f"📝 Evidence added to {curiosity.focus}: "
                f"confidence {old_confidence:.2f} → {curiosity.confidence:.2f}"
                + (f", status {old_status} → {curiosity.status}" if old_status != curiosity.status else "")
            )

        elif curiosity and isinstance(curiosity, CuriosityPattern):
            # For patterns, use simpler confidence update
            old_confidence = curiosity.confidence

            if new_confidence is not None:
                curiosity.confidence = new_confidence
                curiosity.last_updated = datetime.now()
                curiosity.last_updated_reasoning = reasoning

                # Check for significant contradiction
                if effect == "contradicts" and (old_confidence - new_confidence) > 0.3:
                    cascade_result = self._cascade_handler.handle_evidence_contradiction(
                        curiosity=curiosity,
                        old_confidence=old_confidence,
                        new_confidence=new_confidence,
                        session_id=self._session_id,
                        child_id=self.child_id,
                        contradiction_reasoning=reasoning,
                    )
                    if cascade_result.crystal_needs_regeneration:
                        logger.info(f"🔄 Evidence contradiction triggered crystal regeneration need")
            else:
                self._curiosity_manager.on_evidence_added(curiosity_focus, effect)

        logger.info(f"📊 Added evidence to {curiosity_focus}: {effect} (reasoning: {reasoning[:50]}...)")

    # Note: spawn_exploration tool has been removed.
    # Investigations are now started automatically in _handle_wonder
    # when a hypothesis has video_value set.

    def _handle_see_pattern(self, args: Dict[str, Any]):
        """
        Record an emerging pattern across multiple curiosities.

        Required fields:
        - pattern: Short description
        - insight: The cross-domain insight
        - confidence: How sure we are (0-1)
        - connects: Curiosity focuses that contributed (REQUIRED)
        - reasoning: Why this pattern is seen (REQUIRED)
        """
        pattern_desc = args.get("pattern", "")
        insight = args.get("insight", "")
        confidence = args.get("confidence", 0.3)
        domains_involved = args.get("domains_involved", [])
        connects = args.get("connects", [])
        reasoning = args.get("reasoning", "Pattern observed")

        # Create typed Pattern
        pattern = CuriosityPattern.create(
            focus=pattern_desc,
            confidence=confidence,
            reasoning=reasoning,
            domains_involved=domains_involved,
            source_hypotheses=connects,
        )
        pattern.insight = insight  # Store the insight
        self._curiosity_manager.add(pattern)

        # Update contributing hypotheses to track this pattern
        for hyp_focus in connects:
            hyp = self._curiosity_manager.get_by_focus(hyp_focus)
            if hyp and isinstance(hyp, Hypothesis):
                if pattern_desc not in hyp.contributed_to_patterns:
                    hyp.contributed_to_patterns.append(pattern_desc)

        logger.info(f"🔮 Pattern emerged: {pattern_desc} (connects: {connects})")

    def _handle_update_curiosity(self, args: Dict[str, Any]):
        """
        Reassess an existing curiosity based on new understanding.

        Required fields:
        - focus: Curiosity to update
        - change_reasoning: Why this change (REQUIRED)
        - triggered_by: What triggered this (REQUIRED)

        Optional fields:
        - new_fullness_or_confidence
        - new_pull
        - new_status
        """
        focus = args.get("focus", "")
        change_reasoning = args.get("change_reasoning", "")

        if not focus:
            return

        # Update in curiosity manager
        new_value = args.get("new_fullness_or_confidence")
        new_pull = args.get("new_pull")
        new_status = args.get("new_status")

        curiosity = self._curiosity_manager.update_curiosity(
            focus=focus,
            new_fullness_or_confidence=new_value,
            new_pull=new_pull,
            new_status=new_status,
        )

        if curiosity:
            curiosity.last_updated_reasoning = change_reasoning

            # Handle status transitions that trigger cascades
            if new_status == "refuted" and isinstance(curiosity, Hypothesis):
                cascade_result = self._cascade_handler.handle_refutation(
                    hypothesis=curiosity,
                    session_id=self._session_id,
                    child_id=self.child_id,
                    refutation_reasoning=change_reasoning,
                )
                logger.info(f"🔄 Hypothesis refutation cascaded to {len(cascade_result.affected_curiosities)} curiosities")

            elif new_status == "confirmed" and isinstance(curiosity, Hypothesis):
                cascade_result = self._cascade_handler.handle_confirmation(
                    hypothesis=curiosity,
                    session_id=self._session_id,
                    child_id=self.child_id,
                    confirmation_reasoning=change_reasoning,
                )
                logger.info(f"✅ Hypothesis confirmation cascaded to {len(cascade_result.affected_curiosities)} curiosities")

            elif new_status == "dissolved" and isinstance(curiosity, CuriosityPattern):
                cascade_result = self._cascade_handler.handle_pattern_dissolved(
                    pattern=curiosity,
                    session_id=self._session_id,
                    child_id=self.child_id,
                    dissolution_reasoning=change_reasoning,
                )
                logger.info(f"💨 Pattern dissolution cascaded to {len(cascade_result.affected_curiosities)} curiosities")

        logger.info(f"🔄 Updated curiosity: {focus} (reason: {change_reasoning[:50]}...)")

    def _handle_record_milestone(self, args: Dict[str, Any]):
        """Record a developmental milestone."""
        domain = args.get("domain", "general")
        milestone_type = args.get("milestone_type", "achievement")
        age_months = args.get("age_months")

        # Handle birth/pregnancy timeline placement when age_months not specified:
        # - milestone_type='birth' → the birth moment → age_months=0
        # - domain='birth_history' (pregnancy events) → before birth → age_months=-1
        if age_months is None:
            if milestone_type == "birth":
                age_months = 0  # Birth moment
            elif domain == "birth_history":
                age_months = -1  # Pregnancy events appear before birth

        milestone = DevelopmentalMilestone.create(
            description=args["description"],
            domain=domain,
            milestone_type=milestone_type,
            age_months=age_months,
            age_description=args.get("age_description"),
            source="conversation",
            child_birth_date=self.child_birth_date,
        )
        self.understanding.add_milestone(milestone)
        logger.info(f"📌 Milestone recorded: {milestone.description} (domain={milestone.domain}, type={milestone.milestone_type})")

        # Add journal entry for milestones
        entry = JournalEntry.create(
            summary=milestone.description,
            learned=[f"{milestone.domain}: {milestone.description}"],
            significance="notable" if milestone.milestone_type in ["concern", "regression"] else "routine",
            entry_type="milestone_recorded",
        )
        self.journal.append(entry)

    def _handle_set_child_identity(self, args: Dict[str, Any]):
        """Set child identity (name, age, gender).

        Updates both Darshan's internal state AND the Child model via child_service.
        This ensures the ChildSwitcher and other UI components show the correct name.
        """
        # Build data dict for child_service.update_developmental_data
        update_data = {}

        if "name" in args and args["name"]:
            self.child_name = args["name"]
            update_data["child_name"] = args["name"]
            logger.info(f"👶 Child name set: {self.child_name}")

        if "age" in args and args["age"] is not None:
            # Calculate birth date from age
            from datetime import date
            from dateutil.relativedelta import relativedelta
            age_years = float(args["age"])
            age_months = int(age_years * 12)
            today = date.today()
            self.child_birth_date = today - relativedelta(months=age_months)
            update_data["age"] = age_years
            logger.info(f"📅 Child age set: {age_years} years (birth date: {self.child_birth_date})")

        if "gender" in args and args["gender"]:
            self.child_gender = args["gender"]  # Update internal state for prompts
            update_data["gender"] = args["gender"]
            # Also store gender in understanding as an observation
            from app.chitta.models import TemporalFact
            gender_he = "בן" if args["gender"] == "male" else "בת"
            observation = TemporalFact(
                content=f"הילד/ה {gender_he}",
                domain="context",
                source="conversation",
                confidence=0.9,
            )
            self.understanding.add_observation(observation)
            logger.info(f"⚧ Child gender set: {args['gender']}")

        # Update the Child model in child_service so ChildSwitcher etc. see the name
        if update_data:
            from app.services.child_service import get_child_service
            child_service = get_child_service()
            child_service.update_developmental_data(self.child_id, update_data)
            logger.info(f"📝 Updated Child model with identity: {update_data}")

    # ========================================
    # SYNTHESIS
    # ========================================

    def _should_synthesize(self) -> bool:
        """Check if conditions suggest synthesis is ready."""
        # Count high-confidence hypotheses (confirmed or supported)
        confident_count = sum(
            1 for h in self._curiosity_manager.get_by_type("hypothesis")
            if h.status in ["confirmed", "supported"] or h.confidence >= 0.7
        )

        # Conditions for synthesis readiness:
        # - Multiple hypotheses have been confirmed/supported
        # - Multiple stories captured
        # - Sufficient observations accumulated
        return (
            confident_count >= 2 or
            len(self.stories) >= 5 or
            len(self.understanding.observations) >= 10
        )

    def _create_synthesis_report(self) -> SynthesisReport:
        """
        Create synthesis report.

        NOTE: Full implementation would use the strongest model
        for pattern detection via _get_strong_llm().
        """
        # Extract patterns from current understanding
        patterns = list(self.understanding.patterns)

        # Calculate confidence by domain
        confidence_by_domain: Dict[str, float] = {}
        for observation in self.understanding.observations:
            domain = observation.domain or "general"
            if domain not in confidence_by_domain:
                confidence_by_domain[domain] = 0.0
            confidence_by_domain[domain] = min(1.0, confidence_by_domain[domain] + 0.1)

        # Get open questions from curiosities
        open_questions = self._curiosity_manager.get_gaps()

        # Build essence narrative if we have enough understanding
        essence_narrative = None
        if self.understanding.essence and self.understanding.essence.narrative:
            essence_narrative = self.understanding.essence.narrative

        return SynthesisReport(
            essence_narrative=essence_narrative,
            patterns=patterns,
            confidence_by_domain=confidence_by_domain,
            open_questions=open_questions,
        )

    # ========================================
    # STATE ACCESS
    # ========================================

    def get_latest_observation_timestamp(self) -> datetime:
        """
        Get the timestamp of the most recent observation.

        Scans all observations, stories, and evidence to find the newest timestamp.
        Used for Crystal staleness detection.
        """
        timestamps = []

        # Observations
        for observation in self.understanding.observations:
            if hasattr(observation, 't_created') and observation.t_created:
                timestamps.append(observation.t_created)

        # Stories
        for story in self.stories:
            if hasattr(story, 'timestamp') and story.timestamp:
                timestamps.append(story.timestamp)

        # Evidence in investigations (V2: only hypotheses have investigations)
        for curiosity in self._curiosities.get_investigating():
            for evidence in curiosity.investigation.evidence:
                if hasattr(evidence, 'timestamp') and evidence.timestamp:
                    timestamps.append(evidence.timestamp)

        # Return the most recent, or now if no observations yet
        if timestamps:
            return max(timestamps)
        return datetime.now()

    def get_observations_since(self, since: datetime) -> Dict[str, Any]:
        """
        Get all observations made since a given timestamp.

        Used for incremental Crystal updates - we only need to process
        what's new since the last crystallization.
        """
        new_observations = [
            f for f in self.understanding.observations
            if hasattr(f, 't_created') and f.t_created and f.t_created > since
        ]

        new_stories = [
            s for s in self.stories
            if hasattr(s, 'timestamp') and s.timestamp and s.timestamp > since
        ]

        # Get recently updated curiosities
        new_curiosities = [
            c for c in self._curiosity_manager.get_all()
            if c.last_updated and c.last_updated > since
        ]

        return {
            "observations": new_observations,
            "stories": new_stories,
            "curiosities_updated": new_curiosities,
        }

    def is_crystal_stale(self) -> bool:
        """Check if the cached Crystal is stale and needs updating."""
        if not self.crystal:
            return True
        latest = self.get_latest_observation_timestamp()
        return self.crystal.is_stale(latest)

    def get_state_for_persistence(self) -> Dict[str, Any]:
        """Get state for persistence."""
        state = {
            "curiosity_manager": self._curiosity_manager.to_dict(),
            "session_history": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.session_history
            ],
            "session_id": self._session_id,
        }

        # Include child identity (name, gender, birth_date)
        if self.child_name:
            state["name"] = self.child_name
        if self.child_gender:
            state["child_gender"] = self.child_gender
        if self.child_birth_date:
            state["child_birth_date"] = self.child_birth_date.isoformat() if hasattr(self.child_birth_date, 'isoformat') else str(self.child_birth_date)

        # Include understanding (observations, patterns, milestones)
        if self.understanding:
            state["understanding"] = self.understanding.to_dict()

        # Include crystal if present
        if self.crystal:
            state["crystal"] = self.crystal.to_dict()

        # Include shared Letters
        if self.shared_summaries:
            state["shared_summaries"] = [s.to_dict() for s in self.shared_summaries]

        # Include session flags (guided collection mode, etc.)
        if self.session_flags:
            state["session_flags"] = self.session_flags

        return state

    @classmethod
    def from_child_data(
        cls,
        child_id: str,
        child_name: Optional[str],
        understanding_data: Optional[Dict] = None,
        stories_data: Optional[List[Dict]] = None,
        journal_data: Optional[List[Dict]] = None,
        curiosity_manager_data: Optional[Dict] = None,
        session_history_data: Optional[List[Dict]] = None,
        crystal_data: Optional[Dict] = None,
        shared_summaries_data: Optional[List[Dict]] = None,
        child_birth_date: Optional["date"] = None,
        session_flags_data: Optional[Dict] = None,
        child_gender: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> "Darshan":
        """
        Create Darshan from persisted child data.

        This is a factory method for reconstructing Darshan
        from stored state.
        """
        # Build Understanding
        understanding = Understanding()
        if understanding_data:
            # Support both old "facts" and new "observations" keys
            observations_list = understanding_data.get("observations", understanding_data.get("facts", []))
            for obs_data in observations_list:
                observation = TemporalFact(
                    content=obs_data["content"],
                    domain=obs_data.get("domain"),
                    source=obs_data.get("source", "conversation"),
                    confidence=obs_data.get("confidence", 0.7),
                )
                understanding.add_observation(observation)

            # Load milestones
            milestones_list = understanding_data.get("milestones", [])
            for m_data in milestones_list:
                milestone = DevelopmentalMilestone(
                    id=m_data.get("id", generate_id()),
                    description=m_data["description"],
                    age_months=m_data.get("age_months"),
                    age_description=m_data.get("age_description"),
                    domain=m_data.get("domain", "general"),
                    milestone_type=m_data.get("milestone_type", "observation"),
                    source=m_data.get("source", "conversation"),
                    recorded_at=datetime.fromisoformat(m_data["recorded_at"]) if m_data.get("recorded_at") else datetime.now(),
                    notes=m_data.get("notes"),
                )
                understanding.add_milestone(milestone)

            # Load patterns
            patterns_list = understanding_data.get("patterns", [])
            for p_data in patterns_list:
                pattern = Pattern(
                    description=p_data.get("description", ""),
                    domains_involved=p_data.get("domains_involved", p_data.get("domains", [])),
                    confidence=p_data.get("confidence", 0.5),
                    detected_at=datetime.fromisoformat(p_data["detected_at"]) if p_data.get("detected_at") else datetime.now(),
                    title=p_data.get("title"),
                )
                understanding.add_pattern(pattern)

            # Load essence
            if understanding_data.get("essence"):
                e = understanding_data["essence"]
                understanding.essence = Essence(
                    narrative=e.get("narrative", ""),
                    strengths=e.get("strengths", []),
                    temperament=e.get("temperament", []),
                    core_qualities=e.get("core_qualities", []),
                )

        # Build stories
        stories = []
        if stories_data:
            for story_data in stories_data:
                story = Story(
                    summary=story_data["summary"],
                    reveals=story_data.get("reveals", []),
                    domains=story_data.get("domains", []),
                    significance=story_data.get("significance", 0.5),
                )
                stories.append(story)

        # Build journal
        journal = []
        if journal_data:
            for entry_data in journal_data:
                entry = JournalEntry(
                    timestamp=datetime.fromisoformat(entry_data["timestamp"]) if entry_data.get("timestamp") else datetime.now(),
                    summary=entry_data["summary"],
                    learned=entry_data.get("learned", []),
                    significance=entry_data.get("significance", "routine"),
                    entry_type=entry_data.get("entry_type", "insight"),  # Default for old data
                )
                journal.append(entry)

        # Build curiosity manager
        curiosity_manager = None
        if curiosity_manager_data:
            curiosity_manager = CuriosityManager.from_dict(curiosity_manager_data)

        # Build session history
        session_history = []
        if session_history_data:
            for msg_data in session_history_data:
                msg = Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]) if msg_data.get("timestamp") else datetime.now(),
                )
                session_history.append(msg)

        # Build crystal (cached synthesis)
        crystal = None
        if crystal_data:
            crystal = Crystal.from_dict(crystal_data)

        # Build shared Letters
        shared_summaries = []
        if shared_summaries_data:
            for summary_data in shared_summaries_data:
                shared_summaries.append(SharedSummary.from_dict(summary_data))

        darshan = cls(
            child_id=child_id,
            child_name=child_name,
            understanding=understanding,
            stories=stories,
            journal=journal,
            session_history=session_history,
            crystal=crystal,
            shared_summaries=shared_summaries,
            child_birth_date=child_birth_date,
            child_gender=child_gender,
            curiosity_manager=curiosity_manager,
            session_id=session_id,
        )

        # Restore session flags (guided collection mode, etc.)
        if session_flags_data:
            darshan.session_flags = session_flags_data

        # Add "journey started" entry for brand new children (no journal entries yet)
        if not journal:
            name_part = f" עם {child_name}" if child_name else ""
            darshan.journal.append(JournalEntry.create(
                summary=f"התחלנו את המסע{name_part}",
                learned=["מתחילים להכיר"],
                significance="notable",
                entry_type="session_started",
            ))

        return darshan
