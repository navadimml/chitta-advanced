# Curiosity Architecture Specification

**Version**: 2.0
**Date**: December 2025
**Status**: Design Specification

---

## Table of Contents

1. [Core Philosophy](#1-core-philosophy)
2. [Architectural Principles](#2-architectural-principles)
3. [The Two Natures](#3-the-two-natures)
4. [Data Model](#4-data-model)
5. [Event Sourcing](#5-event-sourcing)
6. [LLM Tools](#6-llm-tools)
7. [System Responsibilities](#7-system-responsibilities)
8. [Flows & Cascades](#8-flows--cascades)
9. [Temporal Tracking](#9-temporal-tracking)
10. [Explainability & Audit](#10-explainability--audit)
11. [Fading & Decay](#11-fading--decay)
12. [Crystal Synthesis](#12-crystal-synthesis)

---

## 1. Core Philosophy

### Understanding Emerges Through Curiosity

Chitta builds understanding of a child through **curiosity** — not checklists, not assessments. Curiosities are living entities that evolve, connect, and eventually crystallize into a coherent portrait.

### The Garden Metaphor

```
DISCOVERIES    = Soil        (the ground from which everything grows)
QUESTIONS      = Seeds       (specific inquiries planted in rich soil)
HYPOTHESES     = Plants      (growing theories fed by evidence)
PATTERNS       = Ecosystems  (emergent order from many thriving plants)
CRYSTAL        = Landscape   (the visible whole, the portrait)
```

### The Evolution Path

```
CONVERSATION
     │
     │ [notice]
     ↓
OBSERVATIONS ──────────────────────────────────────┐
     │                                              │
     │ [accumulate in domain]                       │
     ↓                                              │
DISCOVERY ───[notable observation]───> QUESTION    │
     │                                    │         │
     │ [fullness increases]               │         │
     │                                    │ [theory crystallizes]
     │                                    ↓         │
     │                              HYPOTHESIS <────┘
     │                                    │    [add_evidence]
     │                                    │
     │ [confirmed + connects]             │
     │                                    ↓
     └──────────────────────────────> PATTERN
                                          │
                                          │ [synthesize]
                                          ↓
                                       CRYSTAL
```

---

## 2. Architectural Principles

### Principle 1: LLM Decides, System Stores

```
┌─────────────────────────────────────────────────────────────────┐
│                           LLM                                    │
│         (understands meaning, makes semantic decisions)          │
│                                                                  │
│   - Perceives what's notable                                     │
│   - Assesses fullness/confidence                                 │
│   - Sees connections between curiosities                         │
│   - Detects patterns                                             │
│   - Decides when to evolve question → hypothesis                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ decisions with reasoning
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                          SYSTEM                                  │
│         (manages state, no semantic analysis)                    │
│                                                                  │
│   - Stores what LLM decided                                      │
│   - Applies time-based decay (mechanical)                        │
│   - Formats context for LLM                                      │
│   - Provides temporal queries                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**The system NEVER does semantic analysis.** No keyword matching, no string searching, no pattern detection in code.

### Principle 2: Everything Must Be Explainable

Every LLM decision requires:
- **Reasoning**: Why this decision?
- **Evidence refs**: What observations/evidence support it?

This enables:
- Regulatory compliance (GDPR, HIPAA, AI regulations)
- Clinical transparency
- Audit trails

### Principle 3: Full Temporal History

The system tracks a child over **years**. We must:
- Store child's birthdate (age is always calculated)
- Preserve all historical states via event sourcing
- Enable queries like "What did we understand at age 3?"

### Principle 4: Derived Values Are Calculated, Not Stored

```python
# ❌ WRONG: Storing redundant data
child_age_months: int  # Can be calculated from timestamp + birthdate

# ✅ RIGHT: Calculate when needed
def get_age_at(self, timestamp: datetime) -> int:
    return (timestamp - self.child.birthdate).days // 30
```

---

## 3. The Two Natures

Curiosities have two fundamentally different natures:

### Receptive Curiosities (Discovery, Question)

**Nature**: Open, receiving, gathering
**Metric**: Fullness — "How complete is our picture?"
**Mechanism**: Observations fill them up
**Evidence**: Not applicable (no claim to test)

```python
class ReceptiveCuriosity:
    focus: str           # "עולם המשחק שלו"
    fullness: float      # LLM-assessed: 0-1
    pull: float          # LLM-assessed: how urgent?
```

### Assertive Curiosities (Hypothesis, Pattern)

**Nature**: Claiming, testing, proving
**Metric**: Confidence — "How sure are we this is true?"
**Mechanism**: Evidence strengthens or weakens
**Evidence**: Explicitly tracked with effect

```python
class AssertiveCuriosity:
    focus: str           # "רגישות חושית משפיעה על ויסות"
    theory: str          # The testable claim
    confidence: float    # LLM-assessed: 0-1
    pull: float          # LLM-assessed: how urgent?
    evidence: List[Evidence]
```

### Comparison Table

| Aspect | Discovery/Question | Hypothesis/Pattern |
|--------|-------------------|-------------------|
| Nature | Receptive | Assertive |
| Metric | Fullness | Confidence |
| Source | Observations accumulate | Evidence tests claim |
| Evolution | Spawns questions/hypotheses | Confirms into patterns |
| Can be wrong? | No (just incomplete) | Yes (can be refuted) |

---

## 4. Data Model

### 4.1 Child

```python
@dataclass
class Child:
    id: str
    name: str
    birthdate: date
    birthdate_is_estimated: bool = False
    gender: Optional[str] = None

    def age_months_at(self, timestamp: datetime) -> int:
        """Calculate age in months at any point in time."""
        return (timestamp.date() - self.birthdate).days // 30
```

### 4.2 Observation

```python
@dataclass
class Observation:
    id: str
    content: str                          # What was observed
    domain: str                           # Developmental domain

    # Temporal
    timestamp: datetime                   # When we learned this
    refers_to_age_months: Optional[int]   # "At age 2..." (if mentioned)
    when_type: Optional[str]              # "now" | "habitual" | "past"

    # Provenance
    source: str                           # "conversation" | "video" | "story"
    session_id: str

    # Links (set by LLM)
    addresses_curiosity: Optional[str]    # If this answers a curiosity
```

### 4.3 Discovery (Receptive)

```python
@dataclass
class Discovery:
    id: str
    focus: str                    # "עולם המשחק שלו"
    domain: str

    # Current state (LLM-assessed)
    fullness: float               # 0-1
    pull: float                   # 0-1
    status: str                   # "sparse" | "growing" | "rich" | "dormant"

    # Provenance
    created_at: datetime
    created_reasoning: str
    last_updated: datetime
    last_updated_reasoning: str

    # Links
    spawned_curiosities: List[str]  # Questions/hypotheses that emerged
```

### 4.4 Question (Receptive)

```python
@dataclass
class Question:
    id: str
    focus: str                    # "למה משחק לבד?"
    question: str                 # Full question text
    domain: str

    # Current state (LLM-assessed)
    answered: float               # 0-1 (how answered)
    pull: float                   # 0-1
    status: str                   # "open" | "partial" | "answered" | "evolved" | "dormant"

    # Provenance
    created_at: datetime
    created_reasoning: str
    last_updated: datetime
    last_updated_reasoning: str

    # Links
    source_discovery: Optional[str]
    spawned_hypothesis: Optional[str]
    related_observations: List[str]
```

### 4.5 Hypothesis (Assertive)

```python
@dataclass
class Hypothesis:
    id: str
    focus: str                    # Short name: "חושי → ויסות"
    theory: str                   # Full theory (tentative language)
    domain: str

    # Current state (LLM-assessed)
    confidence: float             # 0-1
    pull: float                   # 0-1
    status: str                   # "weak" | "testing" | "supported" | "confirmed" | "refuted" | "transformed" | "dormant"

    # Provenance
    created_at: datetime
    created_reasoning: str
    last_updated: datetime
    last_updated_reasoning: str

    # Evidence chain
    evidence: List[Evidence]

    # Video
    video_appropriate: bool
    video_value: Optional[str]
    video_requested: bool = False

    # Links
    source_question: Optional[str]
    contributed_to_patterns: List[str]
    predecessor: Optional[str]    # If transformed from another
    successor: Optional[str]      # If transformed into another

@dataclass
class Evidence:
    id: str
    content: str
    effect: str                   # "supports" | "contradicts" | "transforms"

    # Provenance
    timestamp: datetime
    session_id: str
    source_observation: str       # Link to observation

    # Explainability (REQUIRED)
    reasoning: str                # Why this effect?
    confidence_before: float
    confidence_after: float
```

### 4.6 Pattern (Assertive)

```python
@dataclass
class Pattern:
    id: str
    focus: str                    # "רגישות חושית היא המפתח"
    insight: str                  # Full cross-domain insight
    domains_involved: List[str]

    # Current state (LLM-assessed)
    confidence: float             # 0-1
    pull: float                   # 0-1
    status: str                   # "emerging" | "solid" | "foundational" | "questioned" | "dissolved"

    # Provenance
    created_at: datetime
    created_reasoning: str
    last_updated: datetime
    last_updated_reasoning: str

    # Links
    source_hypotheses: List[str]
    spawned_questions: List[str]

    # Evidence chain for explainability
    evidence_chain: List[str]     # All observations/evidence that led here
```

### 4.7 Crystal

```python
@dataclass
class Crystal:
    version: int
    created_at: datetime

    # The portrait
    narrative: str                # Who is this child? (2-3 paragraphs)
    essence: str                  # Core nature in one sentence
    strengths: List[Strength]
    edges: List[Edge]
    patterns: List[PatternSummary]
    open_questions: List[str]

    # Provenance
    source_observations: List[str]
    source_patterns: List[str]
    source_hypotheses: List[str]

    # Change tracking
    changes_from_previous: Optional[CrystalDiff]
    change_reasoning: str
    triggered_by_events: List[str]

@dataclass
class CrystalDiff:
    summary: str                  # LLM-generated summary of changes
    narrative_changed: bool
    strengths_added: List[str]
    strengths_removed: List[str]
    edges_added: List[str]
    edges_removed: List[str]
    patterns_added: List[str]
    patterns_removed: List[str]
```

---

## 5. Event Sourcing

Every change is stored as an event. This enables:
- Reconstructing state at any point in time
- Full audit trail
- Regulatory compliance

### Event Structure

```python
@dataclass
class Event:
    id: str
    timestamp: datetime
    session_id: str

    event_type: str               # See event types below
    entity_type: str              # "observation" | "curiosity" | "pattern" | "crystal"
    entity_id: str

    # What changed
    changes: Dict[str, Change]    # {"confidence": {"from": 0.5, "to": 0.7}}

    # Explainability (REQUIRED)
    reasoning: str
    evidence_refs: List[str]

    # Cascade tracking
    triggered_by: Optional[str]   # Parent event
    triggered_events: List[str]   # Child events

@dataclass
class Change:
    field: str
    from_value: Any
    to_value: Any
```

### Event Types

```python
EVENT_TYPES = [
    # Observation events
    "observation_added",

    # Curiosity lifecycle
    "curiosity_created",
    "curiosity_updated",
    "curiosity_evolved",          # Question → Hypothesis
    "curiosity_dormant",
    "curiosity_revived",
    "curiosity_refuted",
    "curiosity_transformed",

    # Evidence events
    "evidence_added",

    # Pattern events
    "pattern_emerged",
    "pattern_strengthened",
    "pattern_questioned",
    "pattern_dissolved",

    # Crystal events
    "crystal_synthesized",
    "crystal_updated",
]
```

### Event Store Interface

```python
class EventStore:
    def append(self, event: Event) -> None:
        """Store an event."""

    def get_events_for(self, entity_id: str) -> List[Event]:
        """Get all events for an entity."""

    def get_events_between(self, start: datetime, end: datetime) -> List[Event]:
        """Get events in time range."""

    def get_events_in_session(self, session_id: str) -> List[Event]:
        """Get all events in a session."""

    def reconstruct_at(self, entity_id: str, timestamp: datetime) -> dict:
        """Reconstruct entity state at a point in time."""
```

---

## 6. LLM Tools

### 6.1 notice — Record Observation

```python
TOOL_NOTICE = {
    "name": "notice",
    "description": """
    Record an observation about the child.

    Use when you learn something from the conversation.
    Link to a curiosity if this observation addresses one.
    """,
    "parameters": {
        "observation": {
            "type": "string",
            "description": "What was observed (concise, situational Hebrew)"
        },
        "domain": {
            "type": "string",
            "enum": ["motor", "social", "emotional", "cognitive", "language",
                     "sensory", "regulation", "sleep", "feeding", "play",
                     "birth_history", "milestones", "medical", "context",
                     "essence", "strengths", "concerns"]
        },
        "when_type": {
            "type": "string",
            "enum": ["now", "days_ago", "weeks_ago", "months_ago",
                     "age_months", "habitual", "past_unspecified"],
            "description": "Temporal reference type"
        },
        "when_value": {
            "type": "number",
            "description": "Numeric value for temporal type"
        },
        "addresses_curiosity": {
            "type": "string",
            "description": "Focus of curiosity this addresses (if any)"
        }
    },
    "required": ["observation", "domain"]
}
```

### 6.2 wonder — Create or Update Curiosity

```python
TOOL_WONDER = {
    "name": "wonder",
    "description": """
    Create a new curiosity or update an existing one.

    Types:
    - discovery: Open exploration of a domain
    - question: Focused inquiry about something specific
    - hypothesis: Testable theory (requires theory field)
    - pattern: Cross-domain insight (requires source_hypotheses)

    You assess fullness/confidence based on what you know.
    You link curiosities when you see connections.
    """,
    "parameters": {
        "focus": {
            "type": "string",
            "description": "What we're curious about"
        },
        "type": {
            "type": "string",
            "enum": ["discovery", "question", "hypothesis", "pattern"]
        },
        "domain": {
            "type": "string",
            "description": "Primary developmental domain"
        },

        # LLM assessment
        "fullness_or_confidence": {
            "type": "number",
            "description": "Your assessment: 0-1"
        },
        "pull": {
            "type": "number",
            "description": "How urgently to explore: 0-1"
        },

        # REQUIRED: Explainability
        "assessment_reasoning": {
            "type": "string",
            "description": "REQUIRED: Why this fullness/confidence level?"
        },
        "evidence_refs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Observation IDs that inform this assessment"
        },

        # Lineage
        "emerges_from": {
            "type": "string",
            "description": "Curiosity this evolved from"
        },

        # Type-specific
        "question": {
            "type": "string",
            "description": "For question: the full question"
        },
        "theory": {
            "type": "string",
            "description": "For hypothesis: the testable theory (tentative language)"
        },
        "video_appropriate": {
            "type": "boolean",
            "description": "For hypothesis: can video test this?"
        },
        "source_hypotheses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "For pattern: hypotheses that form this pattern"
        },
        "insight": {
            "type": "string",
            "description": "For pattern: the cross-domain insight"
        }
    },
    "required": ["focus", "type", "fullness_or_confidence", "assessment_reasoning"]
}
```

### 6.3 add_evidence — Add Evidence to Hypothesis

```python
TOOL_ADD_EVIDENCE = {
    "name": "add_evidence",
    "description": """
    Add evidence to a hypothesis and update your confidence.

    Effects:
    - supports: Evidence strengthens the hypothesis
    - contradicts: Evidence weakens the hypothesis
    - transforms: Evidence changes our understanding
    """,
    "parameters": {
        "curiosity_focus": {
            "type": "string",
            "description": "Focus of the hypothesis"
        },
        "evidence": {
            "type": "string",
            "description": "The evidence content"
        },
        "effect": {
            "type": "string",
            "enum": ["supports", "contradicts", "transforms"]
        },
        "new_confidence": {
            "type": "number",
            "description": "Your updated confidence after this evidence"
        },

        # REQUIRED: Explainability
        "effect_reasoning": {
            "type": "string",
            "description": "REQUIRED: Why does this evidence have this effect?"
        },
        "source_observation": {
            "type": "string",
            "description": "Observation ID this evidence comes from"
        }
    },
    "required": ["curiosity_focus", "evidence", "effect", "effect_reasoning", "source_observation"]
}
```

### 6.4 see_pattern — Recognize Emerging Pattern

```python
TOOL_SEE_PATTERN = {
    "name": "see_pattern",
    "description": """
    When you see a pattern emerging across curiosities, record it.

    A pattern connects multiple hypotheses or observations
    to reveal a cross-domain insight about the child.
    """,
    "parameters": {
        "pattern": {
            "type": "string",
            "description": "Short name for the pattern"
        },
        "insight": {
            "type": "string",
            "description": "The cross-domain insight"
        },
        "confidence": {
            "type": "number",
            "description": "How confident in this pattern: 0-1"
        },

        # REQUIRED: Evidence chain
        "connects": {
            "type": "array",
            "items": {"type": "string"},
            "description": "REQUIRED: IDs of curiosities/observations forming this pattern"
        },
        "reasoning": {
            "type": "string",
            "description": "REQUIRED: How do these pieces connect?"
        }
    },
    "required": ["pattern", "insight", "confidence", "connects", "reasoning"]
}
```

### 6.5 update_curiosity — Reassess Existing Curiosity

```python
TOOL_UPDATE_CURIOSITY = {
    "name": "update_curiosity",
    "description": """
    Reassess an existing curiosity based on new understanding.

    Use when your understanding of a curiosity has shifted.
    """,
    "parameters": {
        "focus": {
            "type": "string",
            "description": "Focus of the curiosity to update"
        },
        "new_fullness_or_confidence": {
            "type": "number",
            "description": "Updated assessment: 0-1"
        },
        "new_pull": {
            "type": "number",
            "description": "Updated urgency: 0-1"
        },
        "new_status": {
            "type": "string",
            "enum": ["active", "dormant", "evolved", "refuted", "confirmed"]
        },

        # REQUIRED: Explainability
        "change_reasoning": {
            "type": "string",
            "description": "REQUIRED: Why is this changing?"
        },
        "triggered_by": {
            "type": "string",
            "description": "What observation/evidence triggered this update"
        }
    },
    "required": ["focus", "change_reasoning", "triggered_by"]
}
```

---

## 7. System Responsibilities

The system handles only mechanical operations — no semantic analysis.

### 7.1 State Storage

```python
class CuriosityStore:
    def save_observation(self, obs: Observation) -> None: ...
    def save_curiosity(self, curiosity: Curiosity) -> None: ...
    def save_pattern(self, pattern: Pattern) -> None: ...
    def save_crystal(self, crystal: Crystal) -> None: ...

    def get_observation(self, id: str) -> Observation: ...
    def get_curiosity(self, focus: str) -> Curiosity: ...
    def get_curiosities_by_type(self, type: str) -> List[Curiosity]: ...
    def get_active_curiosities(self) -> List[Curiosity]: ...
```

### 7.2 Context Formatting

```python
class ContextFormatter:
    def format_for_perception(self, child: Child, session: Session) -> str:
        """
        Format current state for LLM perception phase.

        Includes:
        - Child info
        - Recent observations
        - Active curiosities with visual bars
        - Current patterns
        - Crystal summary (if exists)
        """

    def format_curiosities(self, curiosities: List[Curiosity]) -> str:
        """
        Format curiosities with visual indicators.

        Example output:
        - 🔍 עולם המשחק [████████░░] 80% fullness
        - ❓ למה משחק לבד? [██████░░░░] 60% answered
        - 🎯 חושי → ויסות [███████░░░] 70% confidence
          Theory: רגישות חושית משפיעה על ויסות
          Video appropriate: Yes
        """
```

### 7.3 Time-Based Decay

The ONLY automated logic the system performs:

```python
class DecayManager:
    PULL_DECAY_PER_DAY = 0.01
    DORMANCY_DAYS = {
        "discovery": 21,
        "question": 14,
        "hypothesis": 30,
        "pattern": 45,
    }

    def apply_decay(self, curiosity: Curiosity) -> None:
        """
        Apply time-based pull decay.

        Fullness/confidence do NOT decay — understanding persists.
        Only pull (urgency) fades over time.
        """
        days_since = (datetime.now() - curiosity.last_updated).days
        curiosity.pull = max(0.05, curiosity.pull - days_since * self.PULL_DECAY_PER_DAY)

    def check_dormancy(self, curiosity: Curiosity) -> bool:
        """
        Check if curiosity should become dormant.

        Confirmed/foundational curiosities never go dormant.
        """
        if curiosity.status in ["confirmed", "foundational", "rich"]:
            return False

        days_since = (datetime.now() - curiosity.last_updated).days
        threshold = self.DORMANCY_DAYS.get(curiosity.type, 21)

        return days_since > threshold
```

### 7.4 Event Recording

```python
class EventRecorder:
    def record(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        changes: Dict[str, Change],
        reasoning: str,
        evidence_refs: List[str],
        session_id: str,
        triggered_by: Optional[str] = None,
    ) -> Event:
        """
        Record an event with full provenance.
        """
        event = Event(
            id=generate_id(),
            timestamp=datetime.now(),
            session_id=session_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            triggered_by=triggered_by,
            triggered_events=[],
        )

        self.event_store.append(event)
        return event
```

---

## 8. Flows & Cascades

### 8.1 Observation Added Flow

```
Parent message received
        │
        │ LLM perceives
        ↓
LLM calls notice(observation, domain, addresses_curiosity?)
        │
        ↓
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM ACTIONS                        │
│                                                          │
│  1. Store observation                                    │
│  2. Record "observation_added" event                     │
│  3. If addresses_curiosity:                              │
│     - Link observation to curiosity                      │
│     - Touch curiosity (update last_updated)              │
│                                                          │
│  NOTE: System does NOT assess impact.                    │
│        LLM may call wonder() or update_curiosity()       │
│        to reflect the impact.                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Curiosity Evolution Flow

```
LLM perceives question is substantially answered
AND a theory crystallizes
        │
        │ LLM decides to spawn hypothesis
        ↓
LLM calls wonder(type="hypothesis", emerges_from=question_id)
        │
        ↓
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM ACTIONS                        │
│                                                          │
│  1. Create hypothesis with source_question link          │
│  2. Update question: status="evolved", spawned=hyp_id    │
│  3. Record "curiosity_created" event                     │
│  4. Record "curiosity_evolved" event for question        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Evidence Added Flow

```
LLM perceives new information relates to hypothesis
        │
        ↓
LLM calls add_evidence(focus, evidence, effect, new_confidence, reasoning)
        │
        ↓
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM ACTIONS                        │
│                                                          │
│  1. Create Evidence record with provenance               │
│  2. Add to hypothesis.evidence                           │
│  3. Update hypothesis.confidence to new_confidence       │
│  4. Record "evidence_added" event                        │
│  5. Record "curiosity_updated" event                     │
│                                                          │
│  6. If effect == "refuted" (confidence < 0.2, 2+ contra):│
│     - Update status to "refuted"                         │
│     - TRIGGER: Cascade to source question                │
│     - TRIGGER: Cascade to connected patterns             │
│                                                          │
│  7. If effect == "transforms":                           │
│     - Update status to "transformed"                     │
│     - LLM should spawn refined hypothesis                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 8.4 Refutation Cascade

```
Hypothesis refuted
        │
        ↓
┌─────────────────────────────────────────────────────────┐
│                   CASCADE EFFECTS                        │
│                                                          │
│  1. Source question:                                     │
│     - status → "open"                                    │
│     - spawned_hypothesis → None                          │
│     - answered -= 0.3                                    │
│     - Record "question_reopened" event                   │
│                                                          │
│  2. Connected patterns:                                  │
│     - Recalculate confidence                             │
│     - If < 0.3: status → "questioned"                    │
│     - Record "pattern_weakened" event                    │
│                                                          │
│  3. Crystal:                                             │
│     - Mark for regeneration                              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 8.5 Pattern Emergence Flow

```
LLM perceives connection between confirmed hypotheses
        │
        ↓
LLM calls see_pattern(pattern, insight, confidence, connects, reasoning)
        │
        ↓
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM ACTIONS                        │
│                                                          │
│  1. Create Pattern with source_hypotheses links          │
│  2. Update each source hypothesis:                       │
│     - Add pattern_id to contributed_to_patterns          │
│  3. Record "pattern_emerged" event                       │
│  4. Mark Crystal for regeneration                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 9. Temporal Tracking

### 9.1 Age Calculation

```python
class TemporalContext:
    def __init__(self, child: Child):
        self.child = child

    def age_at(self, timestamp: datetime) -> int:
        """Calculate child's age in months at timestamp."""
        return (timestamp.date() - self.child.birthdate).days // 30

    def current_age(self) -> int:
        """Calculate child's current age in months."""
        return self.age_at(datetime.now())
```

### 9.2 Historical Queries

```python
class TemporalQueries:
    def get_state_at_age(self, child_id: str, age_months: int) -> HistoricalState:
        """
        What was our understanding when child was this age?

        Returns:
        - All observations up to that age
        - Curiosity states at that point
        - Patterns that existed
        - Crystal version at that time
        """

    def get_curiosity_evolution(self, curiosity_id: str) -> CuriosityTimeline:
        """
        How did this curiosity evolve over time?

        Returns timeline of:
        - Fullness/confidence changes
        - Status changes
        - Evidence additions
        - Linked events
        """

    def get_domain_trajectory(self, child_id: str, domain: str) -> DomainTrajectory:
        """
        How has our understanding of this domain evolved?

        Returns:
        - Observation count over time
        - Curiosity evolution in this domain
        - Key milestones
        - Trajectory trend (progressing/stable/regressing)
        """

    def compare_ages(
        self,
        child_id: str,
        age1_months: int,
        age2_months: int
    ) -> AgeComparison:
        """
        Compare understanding at two different ages.

        Useful for progress tracking over years.
        """

    def get_crystal_history(self, child_id: str) -> List[CrystalVersion]:
        """
        All Crystal versions for this child.

        Shows how portrait evolved over time.
        """
```

### 9.3 Developmental Trajectory

```python
@dataclass
class DomainTrajectory:
    domain: str
    child_id: str

    # Timeline
    points: List[TrajectoryPoint]

    # Analysis
    trend: str              # "progressing" | "stable" | "concern" | "catch_up"
    trend_description: str  # LLM-generated description

    # Key moments
    milestones: List[Milestone]
    concerns_emerged: List[ConcernPoint]
    concerns_resolved: List[ResolutionPoint]

@dataclass
class TrajectoryPoint:
    timestamp: datetime
    age_months: int
    observation_count: int
    active_curiosities: List[str]
    patterns_involving: List[str]
    crystal_version: Optional[int]

@dataclass
class LongitudinalInsight:
    """
    Insights that only emerge over time.
    """
    insight: str
    emerged_at_age: int
    time_span_months: int
    trajectory_type: str    # "improvement" | "persistence" | "late_emergence"
    supporting_events: List[str]
    reasoning: str
```

---

## 10. Explainability & Audit

### 10.1 Evidence Chain

Every conclusion must be traceable to source observations:

```
PATTERN: "רגישות חושית היא המפתח"
    │
    └── HYPOTHESIS: "חושי → ויסות"
            │
            ├── EVIDENCE: "מתקשה בסביבות רועשות" (supports)
            │       └── OBSERVATION: "בקניון התמוטט" (session 5)
            │
            ├── EVIDENCE: "מרגיע כשבחושך" (supports)
            │       └── OBSERVATION: "נרגע בחדר חשוך" (session 7)
            │
            └── SOURCE: QUESTION "למה מתפרץ?"
                    └── SOURCE: DISCOVERY "עולם הויסות"
                            └── OBSERVATION: "קשה לו להירגע" (session 2)
```

### 10.2 Explanation Report

```python
@dataclass
class ExplanationReport:
    """
    Regulatory-compliant explanation of any conclusion.
    """
    entity_type: str          # What we're explaining
    entity_id: str
    entity_focus: str

    # Current state
    current_value: float      # Confidence or fullness
    current_status: str

    # The evidence chain
    evidence_timeline: List[EvidenceWithContext]

    # How we got here
    creation_context: CreationContext
    evolution_timeline: List[StateChange]

    # Reasoning at each step
    reasoning_chain: List[ReasoningStep]

    # Summary
    summary: str              # "Based on 12 observations over 8 months..."

    # For regulations
    data_sources: List[str]   # All sessions/messages involved
    observation_count: int
    time_span_days: int

@dataclass
class ReasoningStep:
    timestamp: datetime
    age_months: int
    event_type: str
    reasoning: str
    evidence_refs: List[str]
    value_before: Optional[float]
    value_after: Optional[float]
```

### 10.3 Audit Interface

```python
class AuditInterface:
    def explain_conclusion(self, entity_id: str) -> ExplanationReport:
        """
        Generate full explanation of how we reached this conclusion.
        """

    def get_evidence_chain(self, entity_id: str) -> EvidenceChain:
        """
        Get all evidence that supports/contradicts this entity.
        """

    def get_data_lineage(self, entity_id: str) -> DataLineage:
        """
        Trace back to original conversations.
        """

    def export_audit_log(
        self,
        child_id: str,
        start_date: date,
        end_date: date,
    ) -> AuditLog:
        """
        Export all events for regulatory compliance.
        """
```

---

## 11. Fading & Decay

### 11.1 Pull Decay (Mechanical)

```python
DECAY_RATES = {
    "discovery": 0.008,    # per day
    "question": 0.015,     # per day
    "hypothesis": 0.012,   # per day
    "pattern": 0.006,      # per day (very slow)
}

def apply_pull_decay(curiosity: Curiosity) -> None:
    """
    Pull decays over time without activity.

    NOTE: Fullness and confidence do NOT decay.
    Understanding persists; only urgency fades.
    """
    days_since = (datetime.now() - curiosity.last_updated).days
    rate = DECAY_RATES.get(curiosity.type, 0.01)

    curiosity.pull = max(0.05, curiosity.pull - days_since * rate)
```

### 11.2 Dormancy

```python
DORMANCY_THRESHOLDS = {
    "discovery": 21,       # days
    "question": 14,        # days
    "hypothesis": 30,      # days
    "pattern": 45,         # days
}

def check_dormancy(curiosity: Curiosity) -> None:
    """
    Mark inactive curiosities as dormant.

    Dormant curiosities:
    - Don't appear in active context
    - Can be revived by new activity
    - Preserve all history
    """
    # Never dormant-ize confirmed entities
    if curiosity.status in ["confirmed", "foundational", "rich"]:
        return

    days_since = (datetime.now() - curiosity.last_updated).days
    threshold = DORMANCY_THRESHOLDS.get(curiosity.type, 21)

    if days_since > threshold:
        curiosity.status = "dormant"
```

### 11.3 Revival

```python
def revive_curiosity(curiosity: Curiosity, source: str, session_id: str) -> None:
    """
    Any activity revives a dormant curiosity.
    """
    if curiosity.status != "dormant":
        return

    # Determine revival status
    revival_status = {
        "discovery": "sparse",
        "question": "open",
        "hypothesis": "testing",
        "pattern": "emerging",
    }.get(curiosity.type, "active")

    curiosity.status = revival_status
    curiosity.last_updated = datetime.now()

    # Pull boost
    boost = {
        "observation": 0.15,
        "evidence": 0.2,
        "video": 0.25,
        "parent_mention": 0.12,
    }.get(source, 0.1)

    curiosity.pull = min(0.95, curiosity.pull + boost)

    # Record event
    record_event("curiosity_revived", curiosity, session_id)
```

---

## 12. Crystal Synthesis

### 12.1 Synthesis Triggers

Crystal regeneration is triggered when understanding shifts significantly:

```python
def should_regenerate_crystal(events_since_last: List[Event]) -> bool:
    """
    Should we regenerate the Crystal?
    """
    # Immediate triggers
    immediate_triggers = [
        "pattern_emerged",
        "pattern_dissolved",
        "hypothesis_transformed",
        "video_analyzed",
    ]

    if any(e.event_type in immediate_triggers for e in events_since_last):
        return True

    # Accumulation trigger
    observations = [e for e in events_since_last if e.event_type == "observation_added"]
    if len(observations) >= 5:
        return True

    return False
```

### 12.2 Synthesis Process

```python
def synthesize_crystal(
    child: Child,
    observations: List[Observation],
    curiosities: List[Curiosity],
    patterns: List[Pattern],
    previous_crystal: Optional[Crystal],
) -> Crystal:
    """
    LLM synthesizes all understanding into a coherent portrait.
    """
    # Gather inputs
    rich_discoveries = [c for c in curiosities
                        if c.type == "discovery" and c.fullness > 0.5]

    confirmed_hypotheses = [c for c in curiosities
                            if c.type == "hypothesis" and c.confidence > 0.65]

    solid_patterns = [p for p in patterns if p.confidence > 0.5]

    open_questions = [c for c in curiosities
                      if c.type == "question" and c.answered < 0.5]

    # LLM synthesis
    crystal_data = llm.synthesize(
        prompt=CRYSTAL_SYNTHESIS_PROMPT,
        model="strongest",
        observations=observations,
        discoveries=rich_discoveries,
        hypotheses=confirmed_hypotheses,
        patterns=solid_patterns,
        open_questions=open_questions,
        previous_crystal=previous_crystal,
    )

    # Create Crystal with full provenance
    crystal = Crystal(
        version=(previous_crystal.version + 1) if previous_crystal else 1,
        created_at=datetime.now(),
        **crystal_data,
        source_observations=[o.id for o in observations],
        source_patterns=[p.id for p in solid_patterns],
        source_hypotheses=[h.id for h in confirmed_hypotheses],
    )

    # Compute diff if previous exists
    if previous_crystal:
        crystal.changes_from_previous = compute_crystal_diff(previous_crystal, crystal)

    return crystal
```

### 12.3 Crystal Prompt

```python
CRYSTAL_SYNTHESIS_PROMPT = """
# Crystal Synthesis

You are synthesizing a living portrait of {child_name}.

## Observations
{formatted_observations}

## Discoveries (What We've Explored)
{formatted_discoveries}

## Confirmed Hypotheses
{formatted_hypotheses}

## Patterns
{formatted_patterns}

## Open Questions
{formatted_open_questions}

## Your Task

Synthesize a coherent portrait. Write:

1. **Narrative** (2-3 paragraphs): Who is this child? Paint a vivid picture.

2. **Essence** (1 sentence): Capture their core nature.

3. **Strengths**: What makes them shine? Be specific.

4. **Edges**: Where do they struggle? Use situational language.

5. **Patterns**: The cross-domain insights that explain who they are.

6. **Open Questions**: What are we still curious about?

Write in warm, natural Hebrew. Trust your understanding.
"""
```

---

## Appendix A: Domain List

```python
DOMAINS = [
    # Core developmental
    "motor",
    "social",
    "emotional",
    "cognitive",
    "language",

    # Sensory & regulation
    "sensory",
    "regulation",

    # Daily life
    "sleep",
    "feeding",
    "play",

    # Clinical history
    "birth_history",
    "milestones",
    "medical",

    # Context
    "context",

    # Meta
    "essence",
    "strengths",
    "concerns",
]

CLINICAL_DOMAINS = ["birth_history", "milestones", "sleep", "feeding", "medical"]
```

---

## Appendix B: Status Values

### Discovery Status
- `sparse`: Fullness < 0.3
- `growing`: Fullness 0.3-0.6
- `rich`: Fullness > 0.6
- `dormant`: No activity for 21 days

### Question Status
- `open`: Being explored
- `partial`: Partially answered (0.3-0.6)
- `answered`: Substantially answered (> 0.6)
- `evolved`: Became a hypothesis
- `dormant`: No activity for 14 days

### Hypothesis Status
- `weak`: Confidence < 0.25
- `testing`: Confidence 0.25-0.55
- `supported`: Confidence 0.55-0.75
- `confirmed`: Confidence > 0.75
- `refuted`: Contradicted with low confidence
- `transformed`: Understanding shifted
- `dormant`: No activity for 30 days

### Pattern Status
- `emerging`: Confidence < 0.45
- `solid`: Confidence 0.45-0.7
- `foundational`: Confidence > 0.7
- `questioned`: Source hypotheses weakened
- `dissolved`: Pattern no longer holds

---

## Appendix C: Visual Indicators

For UI display:

```
Discovery:   🔍  Border: emerald
Question:    ❓  Border: blue
Hypothesis:  🎯  Border: purple
Pattern:     🔮  Border: amber

Fullness bar:    [████████░░] 80%
Confidence bar:  [██████░░░░] 60%
Pull indicator:  🔥 (high) | ⚪ (low)
```

---

**End of Specification**
