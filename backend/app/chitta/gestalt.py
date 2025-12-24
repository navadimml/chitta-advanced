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
from typing import List, Dict, Any, Optional

from .curiosity import (
    Curiosity,
    Curiosities,
    InvestigationContext,
    create_hypothesis,
    create_question,
    create_pattern,
    create_discovery,
)
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
        curiosities: Curiosities,
        session_history: List[Message],
        crystal: Optional[Crystal] = None,
        shared_summaries: Optional[List[SharedSummary]] = None,
        child_birth_date: Optional["date"] = None,
        child_gender: Optional[str] = None,
        parent_context: Optional[ParentContext] = None,
        cognitive_turns: Optional[List[CognitiveTurn]] = None,
    ):
        """
        Initialize Darshan.

        Args:
            child_id: Unique identifier for the child
            child_name: Child's name (if known)
            understanding: Current understanding of the child
            stories: Captured stories
            journal: Journal entries
            curiosities: The curiosities manager (includes investigations)
            session_history: Recent conversation history
            crystal: Cached synthesis (patterns, essence, pathways)
            shared_summaries: Previously generated Letters for sharing
            child_birth_date: Child's birth date for age-based temporal calculations
            child_gender: Child's gender for correct pronoun usage (male/female/unknown)
            parent_context: Parent context for gender-appropriate verb forms
            cognitive_turns: Cognitive traces for dashboard (optional, persisted separately)
        """
        self.child_id = child_id
        self.child_name = child_name
        self.understanding = understanding
        self.stories = stories
        self.journal = journal
        self._curiosities = curiosities
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

        # Lazy-loaded LLM providers
        self._llm = None
        self._strong_llm = None

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
    # THREE PUBLIC METHODS - The Surface
    # ========================================

    async def process_message(
        self,
        message: str,
        parent_role: Optional[str] = None,
    ) -> Response:
        """
        Process a parent message with TWO-PHASE architecture.

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
            open_questions=self._curiosities.get_gaps(),
            should_crystallize=should_crystallize,
        )

    def _should_trigger_crystallization(self, tool_calls: List[ToolCall]) -> bool:
        """
        Determine if this turn's learnings warrant background crystallization.

        Important moments that trigger crystallization:
        - Story captured (stories are GOLD)
        - Hypothesis created or spawned exploration
        - Significant evidence added

        We don't crystallize on every turn - only on meaningful learning.
        """
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

    def get_active_curiosities(self) -> List[Curiosity]:
        """What am I curious about right now?"""
        return self._curiosities.get_active(self.understanding)

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

        return f"""
# CHITTA - Perception Phase

You are Chitta, an expert developmental psychologist (0.5-18 years).
You are perceiving what a parent shared and extracting relevant information.
{parent_context_section}{child_gender_section}{crystal_section}{guided_extraction_section}
## WHAT I KNOW ABOUT {child_name}

{format_understanding(context.understanding)}

## WHAT I'M CURIOUS ABOUT

{format_curiosities(context.curiosities)}

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
                # All gaps filled! Transition back to regular conversation
                logger.info(f"All guided collection gaps filled for {self.child_id}, switching to regular mode")

                # Clear guided collection flags - state will be persisted after response
                self.session_flags.pop("preparing_summary_for", None)
                self.session_flags.pop("guided_collection_gaps", None)

                # Get active curiosities for proactive lead
                active_curiosities = self.get_active_curiosities()

                # Build curiosity hint for proactive lead
                curiosity_hint = ""
                if active_curiosities:
                    top_curiosity = active_curiosities[0]
                    question_line = f"Question: {top_curiosity.question}" if getattr(top_curiosity, 'question', None) else ""
                    theory_line = f"Theory: {top_curiosity.theory}" if getattr(top_curiosity, 'theory', None) else ""
                    curiosity_hint = f"""
**PROACTIVE LEAD - Pick up on this curiosity:**
You're curious about: {top_curiosity.focus}
{question_line}
{theory_line}

After acknowledging the summary is ready, naturally lead into this curiosity.
Example: "...ובינתיים, קודם הזכרת ש... סיפרי לי עוד על זה?"
"""

                guided_collection_section = f"""
## GUIDED COLLECTION COMPLETE - TRANSITION TO PROACTIVE CONVERSATION

All the information needed for the summary has been collected.

**YOUR RESPONSE MUST:**
1. Warmly acknowledge completion: "מעולה! יש לי את כל מה שצריך לסיכום"
2. Mention Child Space (חלל הילד): "כשתרצו, אפשר ללכת לחלל הילד וליצור את הסיכום"
3. **PROACTIVELY lead** to the next topic - don't just wait!
{curiosity_hint}
If no specific curiosity, ask about something from what was shared:
"ובינתיים, רציתי לשאול עוד על מה שסיפרת קודם..."

**DO NOT:**
- Say "go back" or "return to" anywhere
- Just say "I'm here if you need" and wait passively
- End with a closed statement
"""

        # Compute guidance from perception
        captured_story = any(tc.name == "capture_story" for tc in perception.tool_calls)
        spawned_curiosity = any(tc.name == "wonder" for tc in perception.tool_calls)
        added_evidence = any(tc.name == "add_evidence" for tc in perception.tool_calls)

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

        guidance = format_turn_guidance(
            captured_story=captured_story,
            spawned_curiosity=spawned_curiosity,
            added_evidence=added_evidence,
            perceived_intent=perception.perceived_intent,
            clinical_gaps=clinical_gaps,
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
        self._curiosities.on_observation_learned(observation)

    def _handle_wonder(self, args: Dict[str, Any]):
        """Spawn a new curiosity."""
        curiosity_type = args.get("type", "question")

        if curiosity_type == "hypothesis":
            curiosity = create_hypothesis(
                focus=args["about"],
                theory=args.get("theory", args["about"]),
                domain=args.get("domain", "general"),
                video_appropriate=args.get("video_appropriate", True),
                video_value=args.get("video_value"),
                video_value_reason=args.get("video_value_reason"),
                certainty=args.get("certainty", 0.3),
            )
        elif curiosity_type == "question":
            curiosity = create_question(
                focus=args["about"],
                question=args.get("question", args["about"]),
                domain=args.get("domain"),
            )
        elif curiosity_type == "pattern":
            curiosity = create_pattern(
                focus=args["about"],
                domains_involved=args.get("domains_involved", []),
                certainty=args.get("certainty", 0.2),
            )
        else:  # discovery
            curiosity = create_discovery(
                focus=args["about"],
                domain=args.get("domain", "essence"),
            )

        self._curiosities.add_curiosity(curiosity)

        # Auto-start investigation for video-valuable hypotheses
        # This enables video suggestion cards without needing spawn_exploration
        if (curiosity.type == "hypothesis" and
            curiosity.video_value is not None and
            curiosity.video_appropriate):
            curiosity.start_investigation()
            logger.info(f"🔬 Auto-started investigation for video-valuable hypothesis: {curiosity.focus}")

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
            self._curiosities.on_domain_touched(domain)

        # Cross-domain stories are GOLD for pattern detection
        # Spawn pattern curiosity when story reveals connections across 2+ domains
        if len(story.domains) >= 2 and story.significance >= 0.5:
            # Check if we already have a pattern curiosity for these domains
            existing_pattern = self._curiosities.find_curiosity_by_domains(
                story.domains
            )
            if not existing_pattern:
                # Create a pattern curiosity connecting these domains
                pattern_focus = f"קשר בין {' ל'.join(story.domains[:3])}"
                pattern_curiosity = create_pattern(
                    focus=pattern_focus,
                    domains_involved=story.domains,
                    certainty=0.3,  # Start tentative
                    pull=0.5 + (story.significance * 0.3),  # Higher pull for significant stories
                )
                self._curiosities.add_curiosity(pattern_curiosity)
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
        """Add evidence to an active investigation."""
        investigation_id = args.get("cycle_id")  # Keep "cycle_id" in args for tool compatibility
        if not investigation_id:
            return

        # Find curiosity by investigation ID
        curiosity = self._curiosities.get_curiosity_by_investigation_id(investigation_id)
        if not curiosity or not curiosity.investigation:
            return

        if curiosity.investigation.status != "active":
            return

        evidence = Evidence.create(
            content=args["evidence"],
            effect=args.get("effect", "supports"),
            source="conversation",
        )
        curiosity.add_evidence(evidence)

        # Update curiosity certainty
        self._curiosities.on_evidence_added(curiosity.focus, evidence.effect)

    # Note: spawn_exploration tool has been removed.
    # Investigations are now started automatically in _handle_wonder
    # when a hypothesis has video_value set.

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
        # Count understood curiosities (completed investigations)
        understood_count = sum(
            1 for c in self._curiosities._dynamic
            if c.status == "understood"
        )

        # Conditions for synthesis readiness:
        # - Multiple curiosities have been understood
        # - Multiple stories captured
        # - Sufficient observations accumulated
        return (
            understood_count >= 2 or
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
        open_questions = self._curiosities.get_gaps()

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

        # Evidence in investigations (from curiosities)
        for curiosity in self._curiosities._dynamic:
            if curiosity.investigation:
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

        new_evidence = []
        for curiosity in self._curiosities._dynamic:
            if curiosity.investigation:
                for evidence in curiosity.investigation.evidence:
                    if hasattr(evidence, 'timestamp') and evidence.timestamp and evidence.timestamp > since:
                        new_evidence.append({
                            "curiosity_focus": curiosity.focus,
                            "evidence": evidence,
                        })

        return {
            "observations": new_observations,
            "stories": new_stories,
            "evidence": new_evidence,
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
            "curiosities": self._curiosities.to_dict(),
            "session_history": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.session_history
            ],
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
        # These need to persist so guided collection survives page reload
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
        curiosities_data: Optional[Dict] = None,
        session_history_data: Optional[List[Dict]] = None,
        crystal_data: Optional[Dict] = None,
        shared_summaries_data: Optional[List[Dict]] = None,
        child_birth_date: Optional["date"] = None,
        session_flags_data: Optional[Dict] = None,
        child_gender: Optional[str] = None,
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

        # Build curiosities
        # Support both old "curiosity_engine" key and new "curiosities" key
        curiosities_data_to_use = curiosities_data
        if curiosities_data_to_use:
            curiosities = Curiosities.from_dict(curiosities_data_to_use)
        else:
            curiosities = Curiosities()

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
            curiosities=curiosities,
            session_history=session_history,
            crystal=crystal,
            shared_summaries=shared_summaries,
            child_birth_date=child_birth_date,
            child_gender=child_gender,
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
