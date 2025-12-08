# Chitta: The פשוט Refactor Plan

**Version**: 4.0 - Minimum NECESSARY Complexity
**Date**: December 2025
**Branch**: `refactor/living-gestalt-architecture`
**Privilege**: Not in production - we can build it right.

**CRITICAL CONSTRAINT**: Tool calls and text responses cannot be combined reliably.
Must preserve **TWO-PHASE** architecture: Phase 1 (extraction with tools), Phase 2 (response without tools).

---

> אנו רואים יופי בכל דבר המכיל את מינימום המורכבות הנדרשת כדי להגשים את ייעודו בעולם
>
> *We see beauty in everything that contains the minimum necessary complexity to fulfill its purpose in the world.*

---

## The Vision (Unchanged)

**Chitta exists to help parents see their children clearly.**

The Gestalt is an **observing intelligence** - not a data container.

Understanding emerges through **curiosity**, not checklists.

**Stories are gold.**

---

## The פשוט Architecture

```
backend/app/chitta/
├── gestalt.py           # ~400 lines - The Living Gestalt
├── curiosity.py         # ~200 lines - Unified curiosity model
├── guidance.py          # ~150 lines - Turn guidance computation
├── story.py             # ~100 lines - Story detection (inline, no separate analyzer)
├── reflection.py        # ~200 lines - Background pattern detection
├── service.py           # ~150 lines - API orchestration
└── models.py            # ~300 lines - All data models
```

**7 files. ~1500 lines total.**

Not 30+ files. Not 5000+ lines. פשוט.

---

## Part 1: The Curiosity Model

One model. Explicit type field. Certainty is independent.

```python
# backend/app/chitta/curiosity.py

@dataclass
class Curiosity:
    """
    Something the Gestalt wants to understand.

    One model serves all four exploration modes:
    - discovery: Open receiving ("Who is this child?")
    - question: Following a thread ("What triggers meltdowns?")
    - hypothesis: Testing a theory ("Music helps him regulate")
    - pattern: Connecting dots across domains ("Sensory input is key")

    Type and certainty are INDEPENDENT:
    - Type = what kind of activity
    - Certainty = how confident within that activity

    You can have a weak hypothesis (certainty=0.3) or a strong discovery (certainty=0.8).
    """
    focus: str                          # What we're curious about
    type: str                           # "discovery" | "question" | "hypothesis" | "pattern"
    activation: float                   # How active right now (0-1)
    certainty: float                    # How confident within this type (0-1)

    # Type-specific fields (used based on type)
    theory: Optional[str] = None        # For hypothesis: the theory to test
    video_appropriate: bool = False     # For hypothesis: can video test this?
    question: Optional[str] = None      # For question: the specific question
    domains_involved: List[str] = field(default_factory=list)  # For pattern: domains connected

    # Common fields
    domain: Optional[str] = None        # Primary developmental domain
    last_activated: datetime = field(default_factory=datetime.now)
    times_explored: int = 0

    def should_spawn_cycle(self) -> bool:
        """Should this curiosity spawn an exploration cycle?"""
        return self.activation > 0.7 and self.times_explored == 0


# What certainty means for each type:
#
# | Type       | Certainty 0.2              | Certainty 0.8                |
# |------------|----------------------------|------------------------------|
# | discovery  | Just starting to see       | Rich picture emerging        |
# | question   | No clues yet               | Almost answered              |
# | hypothesis | Weak theory                | Nearly confirmed             |
# | pattern    | Vague connection           | Clear cross-cutting theme    |
```

---

## Part 2: The Curiosity Engine

Simple activation rules. Four explicit types.

```python
# backend/app/chitta/curiosity.py

class CuriosityEngine:
    """
    Manages the Gestalt's curiosities.

    - 5 perpetual curiosities (always present)
    - Dynamic curiosities (spawned from conversation)
    - Activation rises/falls based on evidence and time
    """

    # The five perpetual curiosities
    PERPETUAL = [
        Curiosity(
            focus="Who is this child?",
            type="discovery",
            activation=0.8,
            certainty=0.1,
            domain="essence"
        ),
        Curiosity(
            focus="What do they love?",
            type="discovery",
            activation=0.6,
            certainty=0.1,
            domain="strengths"
        ),
        Curiosity(
            focus="What's their context?",
            type="discovery",
            activation=0.4,
            certainty=0.1,
            domain="context"
        ),
        Curiosity(
            focus="What brought them here?",
            type="question",
            activation=0.5,
            certainty=0.1,
            question="What concerns brought this family to seek help?",
            domain="concerns"
        ),
        Curiosity(
            focus="What patterns are emerging?",
            type="pattern",
            activation=0.3,
            certainty=0.1,
            domains_involved=[]
        ),
    ]

    def __init__(self, child: Child):
        self.child = child
        self._dynamic: List[Curiosity] = []

    def get_active(self, understanding: Understanding) -> List[Curiosity]:
        """Get all curiosities sorted by activation."""
        all_curiosities = [c.copy() for c in self.PERPETUAL] + self._dynamic

        for c in all_curiosities:
            c.activation = self._calculate_activation(c, understanding)

        return sorted(all_curiosities, key=lambda c: c.activation, reverse=True)

    def _calculate_activation(self, curiosity: Curiosity, understanding: Understanding) -> float:
        """Calculate activation based on gaps, evidence, time."""
        base = curiosity.activation

        # Time decay (2% per day without activity)
        days_since = (datetime.now() - curiosity.last_activated).days
        base -= days_since * 0.02

        # Gap boost (more gaps in this domain = more activation)
        if curiosity.domain:
            gaps = self._count_domain_gaps(curiosity.domain, understanding)
            base += min(gaps * 0.1, 0.3)

        # High certainty dampens activation (we're satisfied)
        if curiosity.certainty > 0.7:
            base -= 0.2

        return max(0.0, min(1.0, base))

    def add_curiosity(self, curiosity: Curiosity):
        """Add a new dynamic curiosity."""
        self._dynamic.append(curiosity)

    def on_fact_learned(self, fact: TemporalFact):
        """Boost activation for related curiosities."""
        for c in self._dynamic + self.PERPETUAL:
            if c.domain == fact.domain:
                c.activation = min(1.0, c.activation + 0.1)
                c.last_activated = datetime.now()

    def on_evidence_added(self, curiosity_focus: str, effect: str):
        """Update certainty based on evidence."""
        for c in self._dynamic:
            if c.focus == curiosity_focus:
                if effect == "supports":
                    c.certainty = min(1.0, c.certainty + 0.1)
                elif effect == "contradicts":
                    c.certainty = max(0.0, c.certainty - 0.15)
                c.last_activated = datetime.now()

    def get_gaps(self) -> List[str]:
        """What do we know we don't know?"""
        gaps = []
        for c in self.PERPETUAL + self._dynamic:
            if c.activation > 0.5 and c.certainty < 0.5:
                if c.type == "question" and c.question:
                    gaps.append(c.question)
                else:
                    gaps.append(c.focus)
        return gaps[:5]
```

---

## Part 3: The Living Gestalt

One file. Three public methods. **TWO-PHASE LLM ARCHITECTURE**.

The Gestalt is an **expert developmental psychologist** (0.5-18 years) - not just a conversationalist.

```python
# backend/app/chitta/gestalt.py (~500 lines)

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

    def __init__(self, child: Child, session: Session, llm_provider: LLMProvider):
        self.child = child
        self.session = session
        self.llm = llm_provider.get('gemini-2.5-flash')
        self._curiosity_engine = CuriosityEngine(child)

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
        # The LLM perceives and extracts - this is where intent
        # and story analysis happen INSIDE the LLM, not keyword matching
        extraction_result = await self._phase1_extract(turn_context)

        # Apply learnings from tool calls
        self._apply_learnings(extraction_result.tool_calls)

        # PHASE 2: Response without tools
        # The LLM generates response with full context
        response_text = await self._phase2_respond(turn_context, extraction_result)

        # Update session
        self.session.add_turn(message, response_text)

        return Response(
            text=response_text,
            curiosities=self.get_active_curiosities(),
            open_questions=self._curiosity_engine.get_gaps(),
        )

    def get_active_curiosities(self) -> List[Curiosity]:
        """What am I curious about right now?"""
        return self._curiosity_engine.get_active(self.child.understanding)

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

        Configuration (from existing code - DO NOT CHANGE):
        - temperature=0.0 (reliable extraction)
        - FunctionCallingConfigMode.ANY (forces tool calls)
        - automatic_function_calling.disable=True
        - maximum_remote_calls=0
        """
        system_prompt = self._build_extraction_prompt(context)

        # CRITICAL LLM CONFIGURATION - preserve from existing code
        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context.this_message}
            ],
            functions=EXTRACTION_TOOLS,  # Tools enabled
            temperature=0.0,              # Low temp for reliable extraction
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfigMode.ANY
                )
            ),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
                maximum_remote_calls=0   # CRITICAL: Must be 0
            ),
        )

        return ExtractionResult(
            tool_calls=response.tool_calls or [],
            perceived_intent=self._infer_intent_from_calls(response.tool_calls),
        )

    async def _phase2_respond(self, context: TurnContext, extraction: ExtractionResult) -> str:
        """
        Phase 2: Response without tools.

        The LLM generates a natural Hebrew response.
        Has full context including what was just extracted.

        Configuration:
        - temperature=0.7 (natural conversation)
        - NO functions (forces text response)
        """
        system_prompt = self._build_response_prompt(context, extraction)

        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                *context.recent_history,  # Conversation history
                {"role": "user", "content": context.this_message}
            ],
            functions=None,  # NO TOOLS - forces text response
            temperature=0.7,
        )

        return response.text

    # ========================================
    # PROMPT BUILDING
    # ========================================

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
        return f"""
# CHITTA - Extraction Phase

You are Chitta, an expert developmental psychologist (0.5-18 years).
You are perceiving what a parent shared and extracting relevant information.

## WHAT I KNOW ABOUT {self.child.identity.name or 'THIS CHILD'}

{format_understanding(context.understanding)}

## WHAT I'M CURIOUS ABOUT

{format_curiosities(context.curiosities)}

## ACTIVE EXPLORATIONS

{format_cycles(self.child.exploration_cycles)}

## YOUR TASK

Read the parent's message and extract what's relevant:

1. **Perceive the message type** - Is this a story? A question? Emotional expression?
   (You understand this from reading - no keywords needed)

2. **If it's a story** - Use capture_story to record what it reveals.
   Stories are GOLD. A skilled observer sees MULTIPLE signals in ONE story.

3. **If you learn something** - Use notice to record observations.

4. **If something sparks curiosity** - Use wonder to spawn exploration.

5. **If evidence relates to active exploration** - Use add_evidence.

## TOOLS AVAILABLE

Use these tools to extract and record what you perceive:
- notice: Record an observation about the child
- wonder: Spawn a new curiosity (discovery/question/hypothesis/pattern)
- capture_story: When a meaningful story is shared - extract what it reveals
- add_evidence: Add evidence to active exploration cycle
- spawn_exploration: Start focused investigation when curiosity is high

RESPOND WITH TOOL CALLS ONLY. No text response in this phase.
"""

    def _build_response_prompt(self, context: TurnContext, extraction: ExtractionResult) -> str:
        """
        Build prompt for Phase 2 (response).

        Turn-specific guidance is computed based on what was extracted.
        """
        # Guidance based on what we just extracted
        guidance = self._compute_guidance_from_extraction(extraction)

        return f"""
# CHITTA - Response Phase

You are Chitta, an expert developmental psychologist (0.5-18 years).
You are responding to what the parent shared.

## IDENTITY
- A helpful guide with deep expertise in child development
- Voice: Warm, professional, Hebrew
- "שמתי לב ש..." not "המערכת זיהתה..."

## WHAT I KNOW ABOUT {self.child.identity.name or 'THIS CHILD'}

{format_understanding(context.understanding)}

## WHAT WE JUST LEARNED

{self._format_extraction_summary(extraction)}

{guidance}

## PRINCIPLES
- Curiosity drives exploration, not checklists
- Stories are GOLD - honor what was shared
- One question at a time, if any
- Follow the flow, don't force agenda

RESPOND IN NATURAL HEBREW. Be warm, professional, insightful.
"""

    def _compute_guidance_from_extraction(self, extraction: ExtractionResult) -> str:
        """
        Compute turn-specific guidance based on what was extracted.

        NOT keyword matching - this is based on what the LLM
        actually understood and extracted in Phase 1.
        """
        captured_story = any(tc.name == 'capture_story' for tc in extraction.tool_calls)
        spawned_curiosity = any(tc.name == 'wonder' for tc in extraction.tool_calls)
        added_evidence = any(tc.name == 'add_evidence' for tc in extraction.tool_calls)

        if captured_story:
            return """
## TURN GUIDANCE: STORY RECEIVED

You just captured a meaningful story. This is GOLD.
- Reflect back what you heard and what it reveals
- Honor the significance - don't rush past it
- Let the parent see their child through new eyes
- Only then, bridge forward naturally

**Do NOT**: Immediately pivot to questions. Miss what it reveals.
"""

        if added_evidence:
            return """
## TURN GUIDANCE: EVIDENCE ADDED

You just added evidence to an active exploration.
- Acknowledge what was shared
- If the exploration is progressing well, share that insight
- Consider if we're close to understanding
"""

        if spawned_curiosity:
            return """
## TURN GUIDANCE: NEW CURIOSITY

Something sparked your curiosity about this child.
- Follow that thread naturally
- Don't make the conversation feel like an interrogation
"""

        # Infer from what tools were NOT called
        if extraction.perceived_intent == 'question':
            return """
## TURN GUIDANCE: QUESTION ASKED

The parent asked a question.
- Answer their question first, directly and helpfully
- Use your developmental psychology expertise
- Then bridge naturally to continue understanding
"""

        if extraction.perceived_intent == 'emotional':
            return """
## TURN GUIDANCE: EMOTION EXPRESSED

The parent is expressing feelings.
- Hold space. Acknowledge what they're feeling.
- You're an expert, but also a human presence.
- Don't rush to problem-solve.
"""

        return """
## TURN GUIDANCE: NATURAL RESPONSE

Respond naturally to what was shared.
- Follow the flow of conversation
- One question at a time, if any
- Let curiosity guide, not agenda
"""

    def _infer_intent_from_calls(self, tool_calls: List[ToolCall]) -> str:
        """
        Infer message intent from what tools were called.

        If capture_story was called → story
        If no extraction tools called but message has '?' → likely question
        This is a HEURISTIC for guidance, not the source of truth.
        """
        if any(tc.name == 'capture_story' for tc in tool_calls):
            return 'story'
        if any(tc.name == 'notice' for tc in tool_calls):
            return 'informational'
        # More heuristics can be added, but the LLM's understanding
        # is the primary source - this just helps with guidance
        return 'conversational'

    # ========================================
    # TOOL CALL HANDLERS (unchanged)
    # ========================================

    def _apply_learnings(self, tool_calls: List[ToolCall]):
        """Apply what LLM learned to child."""
        for call in tool_calls:
            if call.name == 'notice':
                self._handle_notice(call.args)
            elif call.name == 'wonder':
                self._handle_wonder(call.args)
            elif call.name == 'capture_story':
                self._handle_capture_story(call.args)
            elif call.name == 'add_evidence':
                self._handle_add_evidence(call.args)
            elif call.name == 'spawn_exploration':
                self._handle_spawn_exploration(call.args)

    def _handle_notice(self, args: Dict):
        """Notice an observation about the child."""
        fact = TemporalFact(
            content=args['observation'],
            domain=args.get('domain', 'general'),
            source='conversation',
            t_valid=parse_temporal(args.get('when')),
            t_created=datetime.now(),
            confidence=args.get('confidence', 0.7),
        )
        self.child.understanding.add_fact(fact)
        self._curiosity_engine.on_fact_learned(fact)

    def _handle_wonder(self, args: Dict):
        """Spawn a new curiosity."""
        curiosity = Curiosity(
            focus=args['about'],
            type=args.get('type', 'question'),
            activation=0.6,
            certainty=args.get('certainty', 0.3),
            theory=args.get('theory'),
            video_appropriate=args.get('video_appropriate', False),
            question=args.get('question'),
            domains_involved=args.get('domains_involved', []),
            domain=args.get('domain'),
        )
        self._curiosity_engine.add_curiosity(curiosity)

    def _handle_capture_story(self, args: Dict):
        """Capture a story and its developmental signals."""
        story = Story(
            summary=args['summary'],
            reveals=args.get('reveals', []),
            domains=args.get('domains', []),
            significance=args.get('significance', 0.5),
            timestamp=datetime.now(),
        )
        self.child.stories.append(story)

        for domain in story.domains:
            self._curiosity_engine.on_domain_touched(domain)

        self.child.journal.add_entry(JournalEntry(
            timestamp=datetime.now(),
            summary=f"Story captured: {story.summary}",
            learned=story.reveals,
            significance='notable' if story.significance > 0.7 else 'routine',
        ))

    def _handle_add_evidence(self, args: Dict):
        """Add evidence to an active exploration cycle."""
        cycle_id = args.get('cycle_id')
        if not cycle_id:
            return

        cycle = self.child.get_cycle(cycle_id)
        if not cycle or cycle.status != 'active':
            return

        evidence = Evidence(
            content=args['evidence'],
            effect=args.get('effect', 'supports'),
            source='conversation',
            timestamp=datetime.now(),
        )
        cycle.add_evidence(evidence)

        # Update curiosity certainty
        self._curiosity_engine.on_evidence_added(cycle.focus, evidence.effect)

    def _handle_spawn_exploration(self, args: Dict):
        """Spawn a new exploration cycle."""
        cycle = ExplorationCycle(
            id=generate_id(),
            curiosity_type=args.get('type', 'question'),
            focus=args['focus'],
            focus_domain=args.get('domain', 'general'),
            status='active',
            created_at=datetime.now(),
            # Type-specific
            theory=args.get('theory'),
            confidence=0.5 if args.get('type') == 'hypothesis' else None,
            video_appropriate=args.get('video_appropriate', False),
            question=args.get('question'),
            discovery_aspect=args.get('aspect'),
            pattern_observation=args.get('observation'),
        )
        self.child.exploration_cycles.append(cycle)
```

---

## Part 4: Tool Definitions

The LLM uses these tools to learn and explore.

```python
# backend/app/chitta/tools.py

TOOLS = [
    {
        "name": "notice",
        "description": "Record an observation about the child",
        "parameters": {
            "type": "object",
            "properties": {
                "observation": {"type": "string", "description": "What was observed"},
                "domain": {"type": "string", "description": "Developmental domain (social, emotional, motor, cognitive, language, sensory, general)"},
                "when": {"type": "string", "description": "When this was true (e.g., 'yesterday', 'usually', 'at age 2')"},
                "confidence": {"type": "number", "description": "How confident (0-1)"}
            },
            "required": ["observation"]
        }
    },
    {
        "name": "wonder",
        "description": """
Spawn a new curiosity. Choose the type based on what kind of exploration this is:

- discovery: Open receiving, no specific question ("Understanding his essence")
- question: Following a specific thread ("What triggers meltdowns?")
- hypothesis: Testing a theory ("Music helps him regulate")
- pattern: Connecting dots across domains ("Sensory input is key")

Certainty is INDEPENDENT of type - it's how confident you are within that type.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "about": {"type": "string", "description": "What we're curious about"},
                "type": {"type": "string", "enum": ["discovery", "question", "hypothesis", "pattern"]},
                "certainty": {"type": "number", "description": "How confident (0-1). Low=just starting, High=nearly answered/confirmed"},
                "domain": {"type": "string", "description": "Primary developmental domain"},
                # Type-specific
                "theory": {"type": "string", "description": "For hypothesis: the theory to test"},
                "video_appropriate": {"type": "boolean", "description": "For hypothesis: can video test this?"},
                "question": {"type": "string", "description": "For question: the specific question"},
                "domains_involved": {"type": "array", "items": {"type": "string"}, "description": "For pattern: domains connected"}
            },
            "required": ["about", "type"]
        }
    },
    {
        "name": "capture_story",
        "description": """
When a parent shares a meaningful story, capture what it reveals.

Stories are GOLD - a skilled observer sees MULTIPLE signals in ONE story.

Example: "Yesterday at the park, she saw another child crying and went over to pat his back"
reveals: ["empathy", "emotional recognition", "prosocial initiation", "comfort with unfamiliar children"]
""",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Brief summary of the story"},
                "reveals": {"type": "array", "items": {"type": "string"}, "description": "What developmental signals this reveals"},
                "domains": {"type": "array", "items": {"type": "string"}, "description": "Domains touched (social, emotional, motor, cognitive, language, sensory)"},
                "significance": {"type": "number", "description": "How significant (0-1). High = reveals who this child IS"}
            },
            "required": ["summary", "reveals", "domains", "significance"]
        }
    },
    {
        "name": "add_evidence",
        "description": "Add evidence to an active exploration cycle",
        "parameters": {
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string", "description": "ID of the cycle"},
                "evidence": {"type": "string", "description": "The evidence"},
                "effect": {"type": "string", "enum": ["supports", "contradicts", "transforms"], "description": "How this affects the exploration"}
            },
            "required": ["cycle_id", "evidence"]
        }
    },
    {
        "name": "spawn_exploration",
        "description": """
Start a focused exploration cycle when a curiosity is ready for deeper investigation.

Use this when:
- A discovery curiosity needs focused attention
- A question needs systematic exploration
- A hypothesis needs testing (possibly with video)
- A pattern needs validation across domains
""",
        "parameters": {
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "What we're exploring"},
                "type": {"type": "string", "enum": ["discovery", "question", "hypothesis", "pattern"]},
                "domain": {"type": "string", "description": "Primary domain"},
                # Type-specific
                "theory": {"type": "string", "description": "For hypothesis: the theory"},
                "video_appropriate": {"type": "boolean", "description": "For hypothesis: can video test?"},
                "question": {"type": "string", "description": "For question: the question"},
                "aspect": {"type": "string", "description": "For discovery: essence/strengths/context"},
                "observation": {"type": "string", "description": "For pattern: the pattern observed"}
            },
            "required": ["focus", "type"]
        }
    }
]
```

---

## Part 5: Lean Models

Simple data models. No bloat.

```python
# backend/app/chitta/models.py

@dataclass
class JournalEntry:
    """Lean journal entry - 4 fields."""
    timestamp: datetime
    summary: str
    learned: List[str]
    significance: str  # "routine" | "notable" | "breakthrough"


@dataclass
class Story:
    """A captured story."""
    summary: str
    reveals: List[str]
    domains: List[str]
    significance: float
    timestamp: datetime


@dataclass
class Evidence:
    """Evidence for an exploration cycle."""
    content: str
    effect: str  # "supports" | "contradicts" | "transforms"
    source: str
    timestamp: datetime


@dataclass
class ExplorationCycle:
    """
    A focused investigation.

    Supports all 4 types via optional fields.
    """
    id: str
    curiosity_type: str  # "discovery" | "question" | "hypothesis" | "pattern"
    focus: str
    focus_domain: str
    status: str  # "active" | "complete" | "stale"
    created_at: datetime

    # Evidence (all types)
    evidence: List[Evidence] = field(default_factory=list)

    # Type-specific
    theory: Optional[str] = None           # hypothesis
    confidence: Optional[float] = None     # hypothesis
    video_appropriate: bool = False        # hypothesis
    question: Optional[str] = None         # question
    answer_fragments: List[str] = field(default_factory=list)  # question
    discovery_aspect: Optional[str] = None # discovery
    pattern_observation: Optional[str] = None  # pattern
    supporting_cycle_ids: List[str] = field(default_factory=list)  # pattern

    def add_evidence(self, evidence: Evidence):
        self.evidence.append(evidence)
        if self.curiosity_type == 'hypothesis' and self.confidence is not None:
            if evidence.effect == 'supports':
                self.confidence = min(1.0, self.confidence + 0.1)
            elif evidence.effect == 'contradicts':
                self.confidence = max(0.0, self.confidence - 0.15)


@dataclass
class ToolCall:
    """A tool call from LLM."""
    name: str
    args: Dict[str, Any]


@dataclass
class ExtractionResult:
    """
    Result from Phase 1 (extraction with tools).

    Contains the tool calls made by the LLM when perceiving
    and extracting from the parent's message.
    """
    tool_calls: List[ToolCall]
    perceived_intent: str  # 'story' | 'informational' | 'question' | 'emotional' | 'conversational'


@dataclass
class TurnContext:
    """
    Context for processing a turn.

    Built BEFORE Phase 1 - contains everything the extraction LLM needs.
    NOTE: No intent detection here - that happens INSIDE Phase 1 LLM.
    """
    understanding: Understanding
    curiosities: List[Curiosity]
    recent_history: List[Message]
    this_message: str


@dataclass
class Response:
    """Response from the Gestalt."""
    text: str
    curiosities: List[Curiosity]
    open_questions: List[str]


@dataclass
class ConversationMemory:
    """
    Distilled memory from a session.

    Created on session transition (>4 hour gap).
    """
    summary: str
    distilled_at: datetime
    turn_count: int


@dataclass
class SynthesisReport:
    """
    Synthesis report from deep analysis.

    Created by STRONGEST model on demand.
    """
    essence_narrative: Optional[str]
    patterns: List[Pattern]
    confidence_by_domain: Dict[str, float]
    open_questions: List[str]
    created_at: datetime
```

---

## Part 6: Formatting Utilities

Helper functions for building prompts. **No intent detection here** - that happens in Phase 1 LLM.

```python
# backend/app/chitta/formatting.py

def format_understanding(understanding: Understanding) -> str:
    """Format understanding for prompt."""
    if not understanding or not understanding.facts:
        return "Still getting to know this child."

    sections = []

    # Essence (if crystallized)
    if understanding.essence and understanding.essence.narrative:
        sections.append(f"**Who they are**: {understanding.essence.narrative}")

    # Key facts by domain
    domains = {}
    for fact in understanding.facts:
        domain = fact.domain or 'general'
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(fact.content)

    for domain, facts in domains.items():
        sections.append(f"**{domain}**: {'; '.join(facts[:3])}")

    return "\n".join(sections) if sections else "Building understanding..."


def format_curiosities(curiosities: List[Curiosity]) -> str:
    """Format curiosities for prompt with visual activation bars."""
    if not curiosities:
        return "Open to discover who this child is."

    lines = []
    type_icons = {
        "discovery": "🔍",
        "question": "❓",
        "hypothesis": "💡",
        "pattern": "🔗"
    }

    for c in curiosities[:5]:
        bar = "█" * int(c.activation * 10) + "░" * (10 - int(c.activation * 10))
        icon = type_icons.get(c.type, "")
        lines.append(f"- {icon} {c.focus} [{bar}] {int(c.activation * 100)}%")

        # Type-specific details
        if c.type == "hypothesis" and c.theory:
            lines.append(f"  Theory: {c.theory} (confidence: {int(c.certainty * 100)}%)")
        elif c.type == "question" and c.question:
            lines.append(f"  Question: {c.question}")
        elif c.type == "pattern" and c.domains_involved:
            lines.append(f"  Domains: {', '.join(c.domains_involved)}")

    return "\n".join(lines)


def format_cycles(cycles: List[ExplorationCycle]) -> str:
    """Format active exploration cycles for prompt."""
    active = [c for c in cycles if c.status == 'active']
    if not active:
        return "No active explorations."

    lines = []
    for c in active[:3]:
        lines.append(f"- [{c.curiosity_type}] {c.focus} (id: {c.id})")
        if c.curiosity_type == 'hypothesis':
            lines.append(f"  Testing: {c.theory}")
            lines.append(f"  Confidence: {int((c.confidence or 0.5) * 100)}%")
            if c.video_appropriate:
                lines.append(f"  Video appropriate: Yes")
        elif c.curiosity_type == 'question':
            lines.append(f"  Question: {c.question}")
        lines.append(f"  Evidence collected: {len(c.evidence)} pieces")

    return "\n".join(lines)


def format_extraction_summary(extraction: ExtractionResult) -> str:
    """Format what was extracted in Phase 1 for Phase 2 context."""
    if not extraction.tool_calls:
        return "No specific extractions this turn."

    lines = []
    for tc in extraction.tool_calls:
        if tc.name == 'capture_story':
            lines.append(f"📖 Captured story: {tc.args.get('summary', 'story captured')}")
            reveals = tc.args.get('reveals', [])
            if reveals:
                lines.append(f"   Reveals: {', '.join(reveals[:3])}")
        elif tc.name == 'notice':
            lines.append(f"👁 Noticed: {tc.args.get('observation', 'observation')}")
        elif tc.name == 'wonder':
            lines.append(f"💭 New curiosity: {tc.args.get('about', 'something')}")
        elif tc.name == 'add_evidence':
            lines.append(f"📝 Evidence added to exploration")

    return "\n".join(lines) if lines else "Processing naturally."
```

---

## Part 7: Synthesis and Memory Distillation

**No background async processing.**

- Pattern detection: Part of **synthesis** (on demand, strongest model)
- Memory distillation: On **session transition** (>4 hours gap, regular model)

```python
# backend/app/chitta/reflection.py

class SynthesisService:
    """
    Synthesis and memory management.

    NOT background processing. These are synchronous, on-demand operations:
    - Synthesis: Called when user requests report or conditions are ripe
    - Memory distillation: Called when session transitions (>4 hour gap)
    """

    def __init__(self, llm_provider: LLMProvider):
        self.strongest = llm_provider.get('gemini-3-pro-preview')  # Or claude-opus-4-5
        self.regular = llm_provider.get('gemini-2.5-flash')

    async def synthesize(self, child: Child) -> SynthesisReport:
        """
        Create synthesis report with pattern detection.
        Uses STRONGEST model - this is the deep analysis.

        Called:
        - When user requests a report
        - When exploration cycles complete
        - When conditions suggest crystallization is ready
        """
        prompt = f"""
# SYNTHESIS REQUEST

You are synthesizing understanding of {child.identity.name or 'this child'}.

## CURRENT UNDERSTANDING

{child.understanding.to_text()}

## ACTIVE EXPLORATIONS

{self._format_cycles(child.exploration_cycles)}

## CAPTURED STORIES

{self._format_stories(child.stories)}

## YOUR TASK

1. **Detect Patterns**: What themes appear across domains? What connections emerge?

2. **Assess Confidence**: For each area of understanding, how confident are we?

3. **Identify Gaps**: What significant questions remain?

4. **Crystallize Essence**: If enough understanding has emerged, describe who this child IS.

Return structured synthesis with patterns, confidence levels, and narrative.
"""
        result = await self.strongest.generate(prompt)
        return self._parse_synthesis(result)

    async def distill_memory_on_transition(
        self,
        previous_session: Session,
        child: Child
    ) -> ConversationMemory:
        """
        Distill session into memory when session transitions.
        Uses REGULAR model - summarization task.

        Called when:
        - New session starts and previous session exists
        - Gap > 4 hours between last message and new message

        NOT called as background task.
        """
        prompt = f"""
# MEMORY DISTILLATION

Synthesize the previous conversation into memory for the next session.

## PREVIOUS SESSION SUMMARY
{previous_session.memory.summary if previous_session.memory else "First session with this family"}

## CONVERSATION TO DISTILL
{self._format_messages(previous_session.get_all_turns())}

## CHILD CONTEXT
{child.understanding.essence.narrative if child.understanding.essence else "Getting to know this child"}

## YOUR TASK

Create a concise memory that:
1. Preserves key points discussed
2. Notes significant moments or stories shared
3. Captures emotional tone of the conversation
4. Identifies threads to follow up

This memory will be available in the next session to maintain continuity.
"""
        result = await self.regular.generate(prompt)
        return ConversationMemory(
            summary=result.text,
            distilled_at=datetime.now(),
            turn_count=len(previous_session.get_all_turns()),
        )

    def should_synthesize(self, child: Child) -> bool:
        """Check if conditions suggest synthesis is ready."""
        active_cycles = [c for c in child.exploration_cycles if c.status == 'active']
        completed_cycles = [c for c in child.exploration_cycles if c.status == 'complete']

        # Conditions for synthesis readiness:
        # - Multiple cycles have completed
        # - Multiple stories captured
        # - Significant time has passed since last synthesis
        return (
            len(completed_cycles) >= 2 or
            len(child.stories) >= 5 or
            (child.last_synthesis and
             (datetime.now() - child.last_synthesis).days >= 7)
        )
```

---

## Part 8: The Service

Session transition handling. No background async.

```python
# backend/app/chitta/service.py

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

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.synthesis = SynthesisService(llm_provider)
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
        self._persist_gestalt(family_id, gestalt)

        # 4. Return response
        return {
            "response": response.text,
            "curiosity_state": {
                "active_curiosities": [
                    {
                        "focus": c.focus,
                        "type": c.type,
                        "activation": c.activation,
                        "certainty": c.certainty
                    }
                    for c in response.curiosities[:5]
                ],
                "open_questions": response.open_questions,
            },
            "cards": self._derive_cards(gestalt),
        }

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
        child = child_service.get_child(family_id)
        current_session = session_service.get_session(family_id)

        # Check for session transition
        if current_session and self._is_session_transition(current_session):
            # Distill previous session's memory
            memory = await self.synthesis.distill_memory_on_transition(
                current_session, child
            )

            # Start new session with memory
            new_session = session_service.create_session(
                family_id,
                previous_memory=memory
            )

            return LivingGestalt(child, new_session, self.llm_provider)

        # No transition - use existing session or create first
        if not current_session:
            current_session = session_service.create_session(family_id)

        return LivingGestalt(child, current_session, self.llm_provider)

    def _is_session_transition(self, session: Session) -> bool:
        """Check if enough time has passed to consider this a new session."""
        if not session.last_message_at:
            return False

        hours_since_last = (datetime.now() - session.last_message_at).total_seconds() / 3600
        return hours_since_last >= self.SESSION_GAP_HOURS

    def _persist_gestalt(self, family_id: str, gestalt: LivingGestalt):
        """Persist child and session state."""
        child_service.save_child(gestalt.child)
        session_service.save_session(gestalt.session)

    def _derive_cards(self, gestalt: LivingGestalt) -> List[Dict]:
        """Derive action cards from current state."""
        cards = []

        # Video suggestion card for video-appropriate hypotheses
        for cycle in gestalt.child.exploration_cycles:
            if cycle.status == 'active' and cycle.video_appropriate:
                cards.append({
                    "type": "video_suggestion",
                    "reason": f"לחקור: {cycle.focus}",
                    "cycle_id": cycle.id
                })
                break  # One video suggestion at a time

        # Synthesis suggestion when conditions are ripe
        if self.synthesis.should_synthesize(gestalt.child):
            cards.append({
                "type": "synthesis_available",
                "reason": "יש מספיק מידע ליצור סיכום"
            })

        return cards

    async def request_synthesis(self, family_id: str) -> SynthesisReport:
        """
        User-requested synthesis.
        Uses STRONGEST model for deep analysis.
        """
        child = child_service.get_child(family_id)
        report = await self.synthesis.synthesize(child)

        # Update child with synthesis results
        if report.patterns:
            for p in report.patterns:
                child.understanding.add_pattern(p)

        child.last_synthesis = datetime.now()
        child_service.save_child(child)

        return report
```

---

## Part 9: What to Delete

| Current | Action |
|---------|--------|
| `gestalt.py` (1304 lines) | Replace with `gestalt.py` (~400 lines) |
| `tools.py` (1284 lines) | Replace with `tools.py` (~150 lines) |
| All `completeness` | Delete entirely |
| 4 separate curiosity content models | Replace with 1 unified model |
| 15-field JournalEntry | Replace with 4-field model |

---

## Part 10: Implementation Order

### Week 1: Core
1. `curiosity.py` - Unified model + engine
2. `models.py` - Lean data models
3. `gestalt.py` - Living Gestalt with 3 public methods
4. `tools.py` - Tool definitions

### Week 2: Integration
5. `guidance.py` - Turn guidance and prompts
6. `service.py` - Orchestration
7. `reflection.py` - Background processing
8. Update API routes (return curiosity_state, not completeness)

### Week 3: Polish
9. Update frontend (show curiosities, not progress bar)
10. Delete old code
11. Test and document

---

## Part 11: Success Metrics

- [ ] 7 files, ~1800 lines total (slightly more due to two-phase)
- [ ] One Curiosity model with explicit type field
- [ ] Certainty independent of type
- [ ] 4-field JournalEntry
- [ ] No completeness anywhere
- [ ] Gestalt persistent (not rebuilt per message)
- [ ] **Two-phase architecture preserved** (extraction with tools, response without)
- [ ] **Intent detection by LLM, not keywords**
- [ ] Turn guidance computed from extraction results
- [ ] Active cycles show in prompt with type indicator
- [ ] Session transition triggers memory distillation (>4 hour gap)
- [ ] Pattern detection part of synthesis (on demand, strongest model)
- [ ] **No background async processing**

---

## Part 12: What Needs LLM vs What Doesn't

### Needs LLM (Minimum NECESSARY Complexity)

| Task | Why LLM | Model |
|------|---------|-------|
| **Intent Detection** | Understanding parent's meaning requires comprehension | Standard |
| **Story Analysis** | Extracting developmental signals requires expertise | Standard (in Phase 1) |
| **Turn Guidance Basis** | Based on what was extracted in Phase 1 | N/A (code logic) |
| **Pattern Detection** | Cross-domain connections require deep analysis | **Strongest** |
| **Memory Distillation** | Summarization preserving key points | Standard |
| **Response Generation** | Natural Hebrew conversation | Standard |

### Doesn't Need LLM (Simple Code Sufficient)

| Task | Implementation |
|------|----------------|
| Curiosity activation math | `base + evidence_boost - time_decay` |
| Session transition detection | `hours_since_last >= 4` |
| Evidence effect on confidence | `+0.1 supports, -0.15 contradicts` |
| Formatting data for prompts | String interpolation |
| Gestalt state management | Load/save operations |
| Video appropriateness flag | Set by LLM during wonder/spawn, stored as boolean |

---

## Part 13: Testing Strategy

### Unit Tests (No LLM Required)

```python
# backend/tests/test_curiosity.py

class TestCuriosityEngine:
    """Test curiosity activation and management."""

    def test_activation_decay_over_time(self):
        """Activation decays 2% per day without activity."""
        curiosity = Curiosity(
            focus="test",
            type="question",
            activation=0.8,
            certainty=0.5,
            last_activated=datetime.now() - timedelta(days=5)
        )
        engine = CuriosityEngine(mock_child)
        new_activation = engine._calculate_activation(curiosity, mock_understanding)
        assert new_activation == pytest.approx(0.7, abs=0.01)  # 0.8 - 5*0.02

    def test_evidence_boosts_activation(self):
        """New evidence increases related curiosity activation."""
        engine = CuriosityEngine(mock_child)
        engine.add_curiosity(Curiosity(focus="motor skills", type="question", activation=0.5))

        engine.on_fact_learned(TemporalFact(content="walks well", domain="motor"))

        curiosity = engine.get_by_focus("motor skills")
        assert curiosity.activation > 0.5

    def test_high_certainty_dampens_activation(self):
        """High certainty reduces activation (we're satisfied)."""
        curiosity = Curiosity(focus="test", type="hypothesis", activation=0.8, certainty=0.9)
        engine = CuriosityEngine(mock_child)
        new_activation = engine._calculate_activation(curiosity, mock_understanding)
        assert new_activation < 0.8

    def test_four_curiosity_types_supported(self):
        """All four types can be created and behave correctly."""
        types = ["discovery", "question", "hypothesis", "pattern"]
        for t in types:
            c = Curiosity(focus=f"test {t}", type=t, activation=0.5, certainty=0.5)
            assert c.type == t


class TestExplorationCycle:
    """Test exploration cycle behavior."""

    def test_evidence_supports_increases_confidence(self):
        """Supporting evidence increases hypothesis confidence."""
        cycle = ExplorationCycle(
            id="test",
            curiosity_type="hypothesis",
            focus="music helps",
            theory="Music helps regulation",
            confidence=0.5,
        )
        cycle.add_evidence(Evidence(content="calmed with music", effect="supports"))
        assert cycle.confidence == 0.6

    def test_evidence_contradicts_decreases_confidence(self):
        """Contradicting evidence decreases confidence more."""
        cycle = ExplorationCycle(
            id="test",
            curiosity_type="hypothesis",
            focus="music helps",
            theory="Music helps regulation",
            confidence=0.5,
        )
        cycle.add_evidence(Evidence(content="didn't help", effect="contradicts"))
        assert cycle.confidence == 0.35  # -0.15


class TestSessionTransition:
    """Test session transition detection."""

    def test_four_hour_gap_triggers_transition(self):
        """Gap >= 4 hours is a session transition."""
        service = ChittaService(mock_provider)
        session = Session(last_message_at=datetime.now() - timedelta(hours=5))
        assert service._is_session_transition(session) == True

    def test_short_gap_no_transition(self):
        """Gap < 4 hours is same session."""
        service = ChittaService(mock_provider)
        session = Session(last_message_at=datetime.now() - timedelta(hours=2))
        assert service._is_session_transition(session) == False
```

### Integration Tests (With LLM - Mocked or Real)

```python
# backend/tests/test_gestalt_integration.py

class TestTwoPhaseArchitecture:
    """Test the two-phase LLM architecture."""

    @pytest.mark.asyncio
    async def test_phase1_returns_tool_calls_only(self):
        """Phase 1 should return tool calls, not text."""
        gestalt = LivingGestalt(mock_child, mock_session, mock_provider)
        context = TurnContext(
            understanding=mock_understanding,
            curiosities=[],
            recent_history=[],
            this_message="אתמול בגן הוא עזר לילד אחר"
        )

        result = await gestalt._phase1_extract(context)

        assert isinstance(result, ExtractionResult)
        assert len(result.tool_calls) > 0
        # Should capture this as a story
        assert any(tc.name == 'capture_story' for tc in result.tool_calls)

    @pytest.mark.asyncio
    async def test_phase2_returns_text_only(self):
        """Phase 2 should return text response, no tool calls."""
        gestalt = LivingGestalt(mock_child, mock_session, mock_provider)
        context = TurnContext(...)
        extraction = ExtractionResult(tool_calls=[], perceived_intent='conversational')

        response = await gestalt._phase2_respond(context, extraction)

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_story_triggers_capture_story_tool(self):
        """When parent shares story, LLM should call capture_story."""
        gestalt = LivingGestalt(mock_child, mock_session, real_llm_provider)

        response = await gestalt.process_message(
            "אתמול בגן משהו מדהים קרה - דני ראה ילדה בוכה והלך לחבק אותה"
        )

        # Check that story was captured
        assert len(gestalt.child.stories) > 0
        story = gestalt.child.stories[-1]
        assert "empathy" in str(story.reveals).lower() or "אמפתיה" in str(story.reveals)


class TestTurnGuidance:
    """Test that turn guidance changes based on extraction."""

    def test_story_extraction_gives_story_guidance(self):
        """When capture_story was called, guidance reflects story reception."""
        gestalt = LivingGestalt(mock_child, mock_session, mock_provider)
        extraction = ExtractionResult(
            tool_calls=[ToolCall(name='capture_story', args={'summary': 'test'})],
            perceived_intent='story'
        )

        guidance = gestalt._compute_guidance_from_extraction(extraction)

        assert "STORY" in guidance or "GOLD" in guidance

    def test_no_extraction_gives_natural_guidance(self):
        """When no special extraction, guidance is natural."""
        extraction = ExtractionResult(tool_calls=[], perceived_intent='conversational')
        gestalt = LivingGestalt(mock_child, mock_session, mock_provider)

        guidance = gestalt._compute_guidance_from_extraction(extraction)

        assert "NATURAL" in guidance
```

### Conversation Quality Tests (Regression)

```python
# backend/tests/test_conversation_quality.py

class TestConversationQuality:
    """
    Regression tests for conversation quality.

    These tests verify that the refactored system maintains
    or improves conversation quality compared to baseline.
    """

    GOLDEN_CONVERSATIONS = [
        {
            "name": "story_reception",
            "messages": [
                "אתמול בגן דני עזר לילדה שנפלה",
            ],
            "expectations": {
                "should_acknowledge_story": True,
                "should_not_immediately_question": True,
                "should_reflect_meaning": True,
            }
        },
        {
            "name": "direct_question",
            "messages": [
                "מה הדעה שלך על התפתחות השפה שלו?",
            ],
            "expectations": {
                "should_answer_question": True,
                "should_use_expertise": True,
            }
        },
        {
            "name": "emotional_expression",
            "messages": [
                "אני ממש מודאגת לגבי ההתפתחות שלו",
            ],
            "expectations": {
                "should_acknowledge_emotion": True,
                "should_not_dismiss": True,
                "should_hold_space": True,
            }
        },
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("conversation", GOLDEN_CONVERSATIONS)
    async def test_golden_conversation(self, conversation):
        """Test against golden conversation expectations."""
        gestalt = LivingGestalt(fresh_child, fresh_session, real_llm_provider)

        for message in conversation["messages"]:
            response = await gestalt.process_message(message)

        # Evaluate expectations (may need human review or LLM-as-judge)
        evaluation = evaluate_response(response, conversation["expectations"])
        assert evaluation.passes, f"Failed: {evaluation.reasons}"
```

### X-Ray Test Integration

```python
# backend/tests/test_xray_integration.py

class TestXRayCompatibility:
    """Ensure X-Ray testing framework works with refactored architecture."""

    @pytest.mark.asyncio
    async def test_xray_can_trace_two_phases(self):
        """X-Ray should capture both phases of LLM interaction."""
        with xray_trace() as trace:
            gestalt = LivingGestalt(mock_child, mock_session, real_provider)
            await gestalt.process_message("test message")

        # Should have two LLM calls
        llm_calls = [e for e in trace.events if e.type == 'llm_call']
        assert len(llm_calls) == 2
        assert llm_calls[0].metadata['phase'] == 'extraction'
        assert llm_calls[1].metadata['phase'] == 'response'

    @pytest.mark.asyncio
    async def test_xray_captures_tool_calls(self):
        """X-Ray should capture tool calls from Phase 1."""
        with xray_trace() as trace:
            gestalt = LivingGestalt(mock_child, mock_session, real_provider)
            await gestalt.process_message("אתמול קרה משהו מעניין...")

        tool_calls = [e for e in trace.events if e.type == 'tool_call']
        assert len(tool_calls) > 0
```

---

## Part 14: Frontend Changes

### API Response Changes

**Before** (completeness-based):
```json
{
  "response": "...",
  "completeness": {
    "score": 0.65,
    "sections": {
      "basic_info": 0.8,
      "development": 0.5,
      "concerns": 0.7
    }
  }
}
```

**After** (curiosity-based):
```json
{
  "response": "...",
  "curiosity_state": {
    "active_curiosities": [
      {
        "focus": "מה מרגיע אותו?",
        "type": "question",
        "activation": 0.8,
        "certainty": 0.3
      },
      {
        "focus": "מוזיקה עוזרת לו להירגע",
        "type": "hypothesis",
        "activation": 0.7,
        "certainty": 0.6,
        "theory": "מוזיקה עוזרת לו להירגע",
        "video_appropriate": true
      }
    ],
    "open_questions": [
      "מה קורה כשהוא מתוסכל?",
      "איך הוא מתקשר עם ילדים אחרים?"
    ]
  },
  "cards": [
    {
      "type": "video_suggestion",
      "reason": "לחקור: מוזיקה עוזרת לו להירגע",
      "cycle_id": "cycle_123"
    }
  ]
}
```

### Component Changes

#### 1. Replace Progress Bar with Curiosity Display

**Before**: `<ProgressBar value={completeness.score} />`

**After**:
```jsx
// src/components/CuriosityPanel.jsx

function CuriosityPanel({ curiosityState }) {
  const { active_curiosities, open_questions } = curiosityState;

  return (
    <div className="curiosity-panel" dir="rtl">
      <h3>מה אנחנו חוקרים</h3>

      {active_curiosities.map(c => (
        <CuriosityItem key={c.focus} curiosity={c} />
      ))}

      {open_questions.length > 0 && (
        <div className="open-questions">
          <h4>שאלות פתוחות</h4>
          <ul>
            {open_questions.map(q => <li key={q}>{q}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

function CuriosityItem({ curiosity }) {
  const typeIcons = {
    discovery: "🔍",
    question: "❓",
    hypothesis: "💡",
    pattern: "🔗"
  };

  const activationPercent = Math.round(curiosity.activation * 100);

  return (
    <div className={`curiosity-item curiosity-${curiosity.type}`}>
      <span className="type-icon">{typeIcons[curiosity.type]}</span>
      <span className="focus">{curiosity.focus}</span>
      <div className="activation-bar">
        <div
          className="activation-fill"
          style={{ width: `${activationPercent}%` }}
        />
      </div>
      {curiosity.type === 'hypothesis' && curiosity.theory && (
        <div className="theory">
          תיאוריה: {curiosity.theory}
          <span className="certainty">
            (ביטחון: {Math.round(curiosity.certainty * 100)}%)
          </span>
        </div>
      )}
    </div>
  );
}
```

#### 2. Update Cards to Show Exploration Actions

```jsx
// src/components/ActionCard.jsx

function ActionCard({ card }) {
  if (card.type === 'video_suggestion') {
    return (
      <div className="card video-suggestion" dir="rtl">
        <div className="card-icon">🎥</div>
        <div className="card-content">
          <h4>הצעה לצילום</h4>
          <p>{card.reason}</p>
          <button onClick={() => startVideoCapture(card.cycle_id)}>
            התחל צילום
          </button>
        </div>
      </div>
    );
  }

  if (card.type === 'synthesis_available') {
    return (
      <div className="card synthesis-available" dir="rtl">
        <div className="card-icon">📊</div>
        <div className="card-content">
          <h4>סיכום זמין</h4>
          <p>{card.reason}</p>
          <button onClick={() => requestSynthesis()}>
            צור סיכום
          </button>
        </div>
      </div>
    );
  }

  return null;
}
```

#### 3. Deep View Updates

```jsx
// src/components/DeepView.jsx

function DeepView({ childId }) {
  const [synthesis, setSynthesis] = useState(null);
  const [loading, setLoading] = useState(false);

  const requestSynthesis = async () => {
    setLoading(true);
    const report = await api.requestSynthesis(childId);
    setSynthesis(report);
    setLoading(false);
  };

  return (
    <div className="deep-view" dir="rtl">
      <h2>מבט מעמיק</h2>

      {/* Exploration Cycles */}
      <section className="explorations">
        <h3>חקירות פעילות</h3>
        <ExplorationList childId={childId} />
      </section>

      {/* Patterns */}
      <section className="patterns">
        <h3>דפוסים שזוהו</h3>
        <PatternList childId={childId} />
      </section>

      {/* Synthesis */}
      <section className="synthesis">
        <h3>סינתזה</h3>
        {synthesis ? (
          <SynthesisReport report={synthesis} />
        ) : (
          <button onClick={requestSynthesis} disabled={loading}>
            {loading ? 'יוצר סיכום...' : 'צור סיכום'}
          </button>
        )}
      </section>
    </div>
  );
}
```

### Styling Updates

```css
/* src/styles/curiosity.css */

.curiosity-panel {
  padding: 1rem;
  background: var(--surface-color);
  border-radius: 8px;
}

.curiosity-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  border-radius: 4px;
}

.curiosity-discovery { background: rgba(66, 133, 244, 0.1); }
.curiosity-question { background: rgba(251, 188, 4, 0.1); }
.curiosity-hypothesis { background: rgba(52, 168, 83, 0.1); }
.curiosity-pattern { background: rgba(234, 67, 53, 0.1); }

.activation-bar {
  flex: 1;
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.activation-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s ease;
}

.theory {
  width: 100%;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.certainty {
  margin-right: 0.5rem;
  opacity: 0.7;
}
```

### State Management Updates

```jsx
// src/hooks/useChittaState.js

function useChittaState(familyId) {
  const [state, setState] = useState({
    response: null,
    curiosityState: {
      active_curiosities: [],
      open_questions: [],
    },
    cards: [],
  });

  const sendMessage = async (message) => {
    const result = await api.sendMessage(familyId, message);
    setState({
      response: result.response,
      curiosityState: result.curiosity_state,
      cards: result.cards,
    });
    return result;
  };

  const requestSynthesis = async () => {
    const report = await api.requestSynthesis(familyId);
    return report;
  };

  return {
    ...state,
    sendMessage,
    requestSynthesis,
  };
}
```

### Files to Modify

| File | Change |
|------|--------|
| `src/App.jsx` | Remove `completeness` state, add `curiosityState` |
| `src/api/client.js` | Update response parsing |
| `src/components/ProgressBar.jsx` | **DELETE** |
| `src/components/CuriosityPanel.jsx` | **NEW** |
| `src/components/ActionCard.jsx` | Update for new card types |
| `src/components/DeepView.jsx` | Add synthesis request |
| `src/styles/curiosity.css` | **NEW** |

---

## Closing

> פשוט - נטול חלקים עודפים, כזה שמתוכנן בדיוק כדי למלא את מטרתו.
>
> *מינימום המורכבות הנדרשת - not minimum possible, but minimum NECESSARY.*

**7 files. ~1800 lines.**

### The Two-Phase Architecture (Preserved)

```
Message arrives
    ↓
Phase 1: Extraction (with tools, temp=0)
    - LLM perceives and understands
    - Intent detected by comprehension, not keywords
    - Tool calls extract data
    ↓
Apply Learnings
    ↓
Phase 2: Response (without tools, temp=0.7)
    - LLM generates natural Hebrew response
    - Turn guidance based on what was extracted
    ↓
Persist + Return
```

### The Four Exploration Types

- **discovery** - open receiving ("Who is this child?")
- **question** - following a thread ("What triggers meltdowns?")
- **hypothesis** - testing a theory ("Music helps him regulate")
- **pattern** - connecting dots ("Sensory input is key")

Certainty is independent - how confident within each type.

### Identity

Chitta is an **expert developmental psychologist** (0.5-18 years).
Not just a conversationalist. Deep expertise in child development.

### Key Constraints Honored

1. Tool calls and text cannot be combined reliably → **Two-phase preserved**
2. Intent detection needs LLM understanding → **No keyword matching**
3. Pattern detection needs strongest model → **Part of synthesis**
4. Memory distillation on session transition → **No background async**

The water knows how to flow.

---

*Version 4.0 - Minimum NECESSARY Complexity*
*December 2025*
