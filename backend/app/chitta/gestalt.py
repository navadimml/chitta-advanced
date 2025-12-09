"""
The Living Gestalt - The Observing Intelligence

The Gestalt HOLDS, NOTICES, and ACTS.
Child and Session are its memory. The Gestalt is the mind.

THREE PUBLIC METHODS:
1. process_message(message) -> Response
2. get_active_curiosities() -> List[Curiosity]
3. synthesize() -> Optional[SynthesisReport]

CRITICAL: Two-phase LLM architecture required.
- Phase 1: Extraction with tools (LLM understands message, extracts data)
- Phase 2: Response without tools (LLM generates natural response)

Tool calls and text response CANNOT be reliably combined.
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from .curiosity import (
    Curiosity,
    CuriosityEngine,
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
    ExplorationCycle,
    JournalEntry,
    Pattern,
    ToolCall,
    ExtractionResult,
    TurnContext,
    Response,
    SynthesisReport,
    Message,
    Crystal,
    parse_temporal,
)
from .formatting import (
    format_understanding,
    format_curiosities,
    format_cycles,
    format_extraction_summary,
    format_turn_guidance,
    format_crystal,
    build_identity_section,
    build_extraction_tools_description,
    build_response_language_instruction,
)
from .tools import get_extraction_tools

# Import LLM abstraction layer
from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message as LLMMessage, LLMResponse


logger = logging.getLogger(__name__)


class LivingGestalt:
    """
    The observing intelligence - an expert developmental psychologist.

    The Gestalt HOLDS, NOTICES, and ACTS.
    Child and Session are its memory. The Gestalt is the mind.

    CRITICAL: Two-phase architecture required.
    - Phase 1: Extraction with tools (LLM understands message, extracts data)
    - Phase 2: Response without tools (LLM generates natural response)

    Tool calls and text response CANNOT be reliably combined.
    """

    def __init__(
        self,
        child_id: str,
        child_name: Optional[str],
        understanding: Understanding,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        journal: List[JournalEntry],
        curiosity_engine: CuriosityEngine,
        session_history: List[Message],
        crystal: Optional[Crystal] = None,
    ):
        """
        Initialize the Living Gestalt.

        Args:
            child_id: Unique identifier for the child
            child_name: Child's name (if known)
            understanding: Current understanding of the child
            exploration_cycles: Active and past exploration cycles
            stories: Captured stories
            journal: Journal entries
            curiosity_engine: The curiosity engine
            session_history: Recent conversation history
            crystal: Cached synthesis (patterns, essence, pathways)
        """
        self.child_id = child_id
        self.child_name = child_name
        self.understanding = understanding
        self.exploration_cycles = exploration_cycles
        self.stories = stories
        self.journal = journal
        self._curiosity_engine = curiosity_engine
        self.session_history = session_history
        self.crystal = crystal

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

    async def process_message(self, message: str) -> Response:
        """
        Process a parent message with TWO-PHASE architecture.

        Phase 1: Perception + Extraction (with tools)
          - LLM understands intent, context, significance
          - LLM extracts data via tool calls
          - Returns: tool calls only

        Phase 2: Response Generation (without tools)
          - LLM has extraction context
          - LLM generates natural Hebrew response
          - Returns: text only
        """
        # Build context for this turn
        turn_context = self._build_turn_context(message)

        # PHASE 1: Extraction with tools
        extraction_result = await self._phase1_extract(turn_context)

        # Apply learnings from tool calls
        self._apply_learnings(extraction_result.tool_calls)

        # PHASE 2: Response without tools
        response_text = await self._phase2_respond(turn_context, extraction_result)

        # Update session history
        self.session_history.append(Message(role="user", content=message))
        self.session_history.append(Message(role="assistant", content=response_text))

        # Keep history manageable (last 20 messages)
        if len(self.session_history) > 20:
            self.session_history = self.session_history[-20:]

        # Determine if crystallization should be triggered
        should_crystallize = self._should_trigger_crystallization(extraction_result.tool_calls)

        return Response(
            text=response_text,
            curiosities=self.get_active_curiosities(),
            open_questions=self._curiosity_engine.get_gaps(),
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

        important_tools = {"capture_story", "spawn_exploration"}
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
        return self._curiosity_engine.get_active(self.understanding)

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

    async def _phase1_extract(self, context: TurnContext) -> ExtractionResult:
        """
        Phase 1: Extraction with tools.

        The LLM perceives the message and extracts data.
        Intent detection, story analysis, significance assessment
        all happen INSIDE the LLM - not with keyword matching.

        Configuration:
        - temperature=0.0 (reliable extraction)
        - functions=tools (enables function calling)
        """
        system_prompt = self._build_extraction_prompt(context)
        tools = get_extraction_tools()

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
                temperature=0.0,  # Low temp for reliable extraction
                max_tokens=2000,
            )

            # Convert function calls to our ToolCall model
            tool_calls = [
                ToolCall(name=fc.name, args=fc.arguments)
                for fc in llm_response.function_calls
            ]

            return ExtractionResult(
                tool_calls=tool_calls,
                perceived_intent=self._infer_intent_from_calls(tool_calls),
            )

        except Exception as e:
            logger.error(f"Phase 1 extraction error: {e}")
            return ExtractionResult(tool_calls=[], perceived_intent="conversational")

    async def _phase2_respond(self, context: TurnContext, extraction: ExtractionResult) -> str:
        """
        Phase 2: Response without tools.

        The LLM generates a natural Hebrew response.
        Has full context including what was just extracted.

        Configuration:
        - temperature=0.7 (natural conversation)
        - functions=None (forces text response)
        """
        system_prompt = self._build_response_prompt(context, extraction)

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

            return llm_response.content or "אני מתקשה להגיב כרגע. אפשר לנסות שוב?"

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

    def _build_extraction_prompt(self, context: TurnContext) -> str:
        """
        Build prompt for Phase 1 (extraction).

        The LLM is asked to:
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

        return f"""
# CHITTA - Extraction Phase

You are Chitta, an expert developmental psychologist (0.5-18 years).
You are perceiving what a parent shared and extracting relevant information.
{crystal_section}
## WHAT I KNOW ABOUT {child_name}

{format_understanding(context.understanding)}

## WHAT I'M CURIOUS ABOUT

{format_curiosities(context.curiosities)}

## ACTIVE EXPLORATIONS

{format_cycles(self.exploration_cycles)}

## YOUR TASK

Read the parent's message and extract what's relevant:

1. **Perceive the message type** - Is this a story? A question? Emotional expression?
   (You understand this from reading - no keywords needed)

2. **If it's a story** - Use capture_story to record what it reveals.
   Stories are GOLD. A skilled observer sees MULTIPLE signals in ONE story.

3. **If you learn something** - Use notice to record observations.

4. **If something sparks curiosity** - Use wonder to spawn exploration.

5. **If evidence relates to active exploration** - Use add_evidence.

{build_extraction_tools_description()}
"""

    def _build_response_prompt(self, context: TurnContext, extraction: ExtractionResult) -> str:
        """
        Build prompt for Phase 2 (response).

        Turn-specific guidance is computed based on what was extracted.
        Crystal provides holistic context for more insightful responses.
        """
        child_name = self.child_name or "THIS CHILD"

        # Include Crystal if available - provides holistic understanding
        crystal_section = ""
        if self.crystal:
            crystal_section = f"""
## HOLISTIC UNDERSTANDING (Crystal)

{format_crystal(self.crystal)}
"""

        # Compute guidance from extraction
        captured_story = any(tc.name == "capture_story" for tc in extraction.tool_calls)
        spawned_curiosity = any(tc.name == "wonder" for tc in extraction.tool_calls)
        added_evidence = any(tc.name == "add_evidence" for tc in extraction.tool_calls)

        guidance = format_turn_guidance(
            captured_story=captured_story,
            spawned_curiosity=spawned_curiosity,
            added_evidence=added_evidence,
            perceived_intent=extraction.perceived_intent,
        )

        return f"""
# CHITTA - Response Phase

You are Chitta, an expert developmental psychologist (0.5-18 years).
You are responding to what the parent shared.

{build_identity_section()}
{crystal_section}
## WHAT I KNOW ABOUT {child_name}

{format_understanding(context.understanding)}

## WHAT WE JUST LEARNED

{format_extraction_summary(extraction)}

{guidance}

{build_response_language_instruction()}

## PRINCIPLES

- Curiosity drives exploration, not checklists
- Stories are GOLD - honor what was shared
- One question at a time, if any
- Follow the flow, don't force agenda
- Use the holistic understanding (Crystal) to connect what's shared to patterns

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

    def _apply_learnings(self, tool_calls: List[ToolCall]):
        """Apply what LLM learned to child state."""
        for call in tool_calls:
            try:
                if call.name == "notice":
                    self._handle_notice(call.args)
                elif call.name == "wonder":
                    self._handle_wonder(call.args)
                elif call.name == "capture_story":
                    self._handle_capture_story(call.args)
                elif call.name == "add_evidence":
                    self._handle_add_evidence(call.args)
                elif call.name == "spawn_exploration":
                    self._handle_spawn_exploration(call.args)
            except Exception as e:
                logger.error(f"Error handling tool call {call.name}: {e}")

    def _handle_notice(self, args: Dict[str, Any]):
        """Notice an observation about the child."""
        fact = TemporalFact(
            content=args["observation"],
            domain=args.get("domain", "general"),
            source="conversation",
            t_valid=parse_temporal(args.get("when")),
            t_created=datetime.now(),
            confidence=args.get("confidence", 0.7),
        )
        self.understanding.add_fact(fact)
        self._curiosity_engine.on_fact_learned(fact)

    def _handle_wonder(self, args: Dict[str, Any]):
        """Spawn a new curiosity."""
        curiosity_type = args.get("type", "question")

        if curiosity_type == "hypothesis":
            curiosity = create_hypothesis(
                focus=args["about"],
                theory=args.get("theory", args["about"]),
                domain=args.get("domain", "general"),
                video_appropriate=args.get("video_appropriate", True),
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

        self._curiosity_engine.add_curiosity(curiosity)

    def _handle_capture_story(self, args: Dict[str, Any]):
        """Capture a story and its developmental signals."""
        story = Story.create(
            summary=args["summary"],
            reveals=args.get("reveals", []),
            domains=args.get("domains", []),
            significance=args.get("significance", 0.5),
        )
        self.stories.append(story)

        # Touch domains in curiosity engine
        for domain in story.domains:
            self._curiosity_engine.on_domain_touched(domain)

        # Add journal entry
        entry = JournalEntry.create(
            summary=f"Story captured: {story.summary}",
            learned=story.reveals,
            significance="notable" if story.significance > 0.7 else "routine",
        )
        self.journal.append(entry)

    def _handle_add_evidence(self, args: Dict[str, Any]):
        """Add evidence to an active exploration cycle."""
        cycle_id = args.get("cycle_id")
        if not cycle_id:
            return

        cycle = self._get_cycle(cycle_id)
        if not cycle or cycle.status != "active":
            return

        evidence = Evidence.create(
            content=args["evidence"],
            effect=args.get("effect", "supports"),
            source="conversation",
        )
        cycle.add_evidence(evidence)

        # Update curiosity certainty
        self._curiosity_engine.on_evidence_added(cycle.focus, evidence.effect)

    def _handle_spawn_exploration(self, args: Dict[str, Any]):
        """Spawn a new exploration cycle."""
        exploration_type = args.get("type", "question")

        if exploration_type == "hypothesis":
            cycle = ExplorationCycle.create_for_hypothesis(
                focus=args["focus"],
                theory=args.get("theory", args["focus"]),
                domain=args.get("domain", "general"),
                video_appropriate=args.get("video_appropriate", True),
            )
        elif exploration_type == "question":
            cycle = ExplorationCycle.create_for_question(
                focus=args["focus"],
                question=args.get("question", args["focus"]),
                domain=args.get("domain", "general"),
            )
        elif exploration_type == "pattern":
            cycle = ExplorationCycle.create_for_pattern(
                focus=args["focus"],
                observation=args.get("observation", ""),
                domains=[args.get("domain", "general")],
            )
        else:  # discovery
            cycle = ExplorationCycle.create_for_discovery(
                focus=args["focus"],
                aspect=args.get("aspect", "essence"),
                domain=args.get("domain", "general"),
            )

        self.exploration_cycles.append(cycle)

        # Link curiosity to cycle
        self._curiosity_engine.link_to_cycle(args["focus"], cycle.id)

    def _get_cycle(self, cycle_id: str) -> Optional[ExplorationCycle]:
        """Get exploration cycle by ID."""
        for cycle in self.exploration_cycles:
            if cycle.id == cycle_id:
                return cycle
        return None

    # ========================================
    # SYNTHESIS
    # ========================================

    def _should_synthesize(self) -> bool:
        """Check if conditions suggest synthesis is ready."""
        completed_cycles = [c for c in self.exploration_cycles if c.status == "complete"]

        # Conditions for synthesis readiness:
        # - Multiple cycles have completed
        # - Multiple stories captured
        # - Sufficient facts accumulated
        return (
            len(completed_cycles) >= 2 or
            len(self.stories) >= 5 or
            len(self.understanding.facts) >= 10
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
        for fact in self.understanding.facts:
            domain = fact.domain or "general"
            if domain not in confidence_by_domain:
                confidence_by_domain[domain] = 0.0
            confidence_by_domain[domain] = min(1.0, confidence_by_domain[domain] + 0.1)

        # Get open questions from curiosity engine
        open_questions = self._curiosity_engine.get_gaps()

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

        Scans all facts, stories, and evidence to find the newest timestamp.
        Used for Crystal staleness detection.
        """
        timestamps = []

        # Facts
        for fact in self.understanding.facts:
            if hasattr(fact, 't_created') and fact.t_created:
                timestamps.append(fact.t_created)

        # Stories
        for story in self.stories:
            if hasattr(story, 'timestamp') and story.timestamp:
                timestamps.append(story.timestamp)

        # Evidence in exploration cycles
        for cycle in self.exploration_cycles:
            for evidence in cycle.evidence:
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
        new_facts = [
            f for f in self.understanding.facts
            if hasattr(f, 't_created') and f.t_created and f.t_created > since
        ]

        new_stories = [
            s for s in self.stories
            if hasattr(s, 'timestamp') and s.timestamp and s.timestamp > since
        ]

        new_evidence = []
        for cycle in self.exploration_cycles:
            for evidence in cycle.evidence:
                if hasattr(evidence, 'timestamp') and evidence.timestamp and evidence.timestamp > since:
                    new_evidence.append({
                        "cycle_focus": cycle.focus,
                        "evidence": evidence,
                    })

        return {
            "facts": new_facts,
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
            "curiosity_engine": self._curiosity_engine.to_dict(),
            "session_history": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.session_history
            ],
        }

        # Include crystal if present
        if self.crystal:
            state["crystal"] = self.crystal.to_dict()

        return state

    @classmethod
    def from_child_data(
        cls,
        child_id: str,
        child_name: Optional[str],
        understanding_data: Optional[Dict] = None,
        exploration_cycles_data: Optional[List[Dict]] = None,
        stories_data: Optional[List[Dict]] = None,
        journal_data: Optional[List[Dict]] = None,
        curiosity_data: Optional[Dict] = None,
        session_history_data: Optional[List[Dict]] = None,
        crystal_data: Optional[Dict] = None,
    ) -> "LivingGestalt":
        """
        Create a LivingGestalt from persisted child data.

        This is a factory method for reconstructing the Gestalt
        from stored state.
        """
        # Build Understanding
        understanding = Understanding()
        if understanding_data:
            for fact_data in understanding_data.get("facts", []):
                fact = TemporalFact(
                    content=fact_data["content"],
                    domain=fact_data.get("domain"),
                    source=fact_data.get("source", "conversation"),
                    confidence=fact_data.get("confidence", 0.7),
                )
                understanding.add_fact(fact)

        # Build exploration cycles
        exploration_cycles = []
        if exploration_cycles_data:
            for cycle_data in exploration_cycles_data:
                # Build video scenarios
                video_scenarios = []
                for scenario_data in cycle_data.get("video_scenarios", []):
                    from .models import VideoScenario
                    scenario = VideoScenario(
                        id=scenario_data["id"],
                        title=scenario_data["title"],
                        what_to_film=scenario_data["what_to_film"],
                        rationale_for_parent=scenario_data.get("rationale_for_parent", ""),
                        duration_suggestion=scenario_data.get("duration_suggestion", "3-5 דקות"),
                        example_situations=scenario_data.get("example_situations", []),
                        target_hypothesis_id=scenario_data.get("target_hypothesis_id", ""),
                        what_we_hope_to_learn=scenario_data.get("what_we_hope_to_learn", ""),
                        focus_points=scenario_data.get("focus_points", []),
                        category=scenario_data.get("category", "exploration"),
                        status=scenario_data.get("status", "pending"),
                        video_path=scenario_data.get("video_path"),
                        uploaded_at=datetime.fromisoformat(scenario_data["uploaded_at"]) if scenario_data.get("uploaded_at") else None,
                        analysis_result=scenario_data.get("analysis_result"),
                        analyzed_at=datetime.fromisoformat(scenario_data["analyzed_at"]) if scenario_data.get("analyzed_at") else None,
                    )
                    video_scenarios.append(scenario)

                # Build evidence
                evidence_list = []
                for evidence_data in cycle_data.get("evidence", []):
                    from .models import Evidence
                    evidence = Evidence(
                        content=evidence_data["content"],
                        effect=evidence_data.get("effect", "supports"),
                        source=evidence_data.get("source", "conversation"),
                        timestamp=datetime.fromisoformat(evidence_data["timestamp"]) if evidence_data.get("timestamp") else datetime.now(),
                    )
                    evidence_list.append(evidence)

                cycle = ExplorationCycle(
                    id=cycle_data["id"],
                    curiosity_type=cycle_data.get("curiosity_type", "question"),
                    focus=cycle_data["focus"],
                    focus_domain=cycle_data.get("focus_domain", "general"),
                    status=cycle_data.get("status", "active"),
                    theory=cycle_data.get("theory"),
                    confidence=cycle_data.get("confidence"),
                    video_appropriate=cycle_data.get("video_appropriate", False),
                    question=cycle_data.get("question"),
                    # Video consent fields
                    video_accepted=cycle_data.get("video_accepted", False),
                    video_declined=cycle_data.get("video_declined", False),
                    video_suggested_at=datetime.fromisoformat(cycle_data["video_suggested_at"]) if cycle_data.get("video_suggested_at") else None,
                    video_scenarios=video_scenarios,
                    evidence=evidence_list,
                )
                exploration_cycles.append(cycle)

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
                )
                journal.append(entry)

        # Build curiosity engine
        if curiosity_data:
            curiosity_engine = CuriosityEngine.from_dict(curiosity_data)
        else:
            curiosity_engine = CuriosityEngine()

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

        return cls(
            child_id=child_id,
            child_name=child_name,
            understanding=understanding,
            exploration_cycles=exploration_cycles,
            stories=stories,
            journal=journal,
            curiosity_engine=curiosity_engine,
            session_history=session_history,
            crystal=crystal,
        )
