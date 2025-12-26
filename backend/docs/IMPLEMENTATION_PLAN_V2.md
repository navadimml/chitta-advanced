# Curiosity Architecture V2 - Implementation Plan

**Branch**: `feature/curiosity-architecture-v2`
**Date**: December 2025
**Status**: Planning

---

## Executive Summary

This plan refactors the Chitta curiosity system from the current unified `Curiosity` model with a single `certainty` metric to the new architecture that introduces:

1. **Two Natures Split**: Receptive (Discovery/Question with `fullness`) vs Assertive (Hypothesis/Pattern with `confidence`)
2. **Event Sourcing**: All state changes stored as immutable events for audit trails
3. **Required Provenance**: Every LLM decision requires `reasoning` and `evidence_refs`
4. **Pattern as Curiosity Type**: Patterns become first-class curiosities with lineage
5. **Crystal Versioning**: Versioned crystals with diffs and change tracking

Since there is **no existing data**, this is a clean refactor - we replace the old implementation entirely.

---

## Current vs Target Comparison

| Aspect | Current | Target |
|--------|---------|--------|
| Curiosity Model | Single `Curiosity` class | Type hierarchy (Discovery, Question, Hypothesis, Pattern) |
| Metric | `certainty` for all | `fullness` (receptive) / `confidence` (assertive) |
| State Changes | Direct mutation | Event sourcing with full audit trail |
| Provenance | Optional/missing | Required `reasoning` + `evidence_refs` |
| Age Storage | `child_age_months` stored | Calculated from `birthdate + timestamp` |
| Patterns | Separate in `Understanding` | First-class `Pattern` curiosity type |
| Crystal | Single state | Versioned with diffs |
| Pull Management | Calculated in code | LLM sets pull, system applies decay only |

---

## Phase 1: Core Data Models

**Goal**: Replace old Curiosity with new type-specific models.

### 1.1 New Model Hierarchy

**New file**: `/backend/app/chitta/curiosity_types.py`

```python
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class BaseCuriosity(ABC):
    """Base class for all curiosity types."""
    id: str
    focus: str
    domain: str
    pull: float  # 0-1, LLM sets initial, system applies decay
    status: str  # Type-specific statuses

    # Temporal
    created_at: datetime
    last_updated: datetime

    # REQUIRED Provenance
    created_reasoning: str
    last_updated_reasoning: str


@dataclass
class ReceptiveCuriosity(BaseCuriosity):
    """Curiosities that receive/gather information."""
    fullness: float  # 0-1, how complete is our picture


@dataclass
class Discovery(ReceptiveCuriosity):
    """Open exploration of a domain."""
    # status: "sparse" | "growing" | "rich" | "dormant"
    spawned_curiosities: List[str] = field(default_factory=list)


@dataclass
class Question(ReceptiveCuriosity):
    """Focused inquiry about something specific."""
    # status: "open" | "partial" | "answered" | "evolved" | "dormant"
    question: str = ""
    source_discovery: Optional[str] = None
    spawned_hypothesis: Optional[str] = None
    related_observations: List[str] = field(default_factory=list)


@dataclass
class AssertiveCuriosity(BaseCuriosity):
    """Curiosities that make claims to be tested."""
    confidence: float  # 0-1, how sure are we this is true
    evidence: List["Evidence"] = field(default_factory=list)


@dataclass
class Hypothesis(AssertiveCuriosity):
    """Testable theory."""
    # status: "weak" | "testing" | "supported" | "confirmed" | "refuted" | "transformed" | "dormant"
    theory: str = ""
    video_appropriate: bool = False
    video_value: Optional[str] = None
    video_value_reason: Optional[str] = None
    source_question: Optional[str] = None
    contributed_to_patterns: List[str] = field(default_factory=list)
    predecessor: Optional[str] = None
    successor: Optional[str] = None


@dataclass
class Pattern(AssertiveCuriosity):
    """Cross-domain insight (Pattern as curiosity type)."""
    # status: "emerging" | "solid" | "foundational" | "questioned" | "dissolved"
    insight: str = ""
    domains_involved: List[str] = field(default_factory=list)
    source_hypotheses: List[str] = field(default_factory=list)
    spawned_questions: List[str] = field(default_factory=list)
    evidence_chain: List[str] = field(default_factory=list)
```

### 1.2 Update Evidence Model

**Modify**: `/backend/app/chitta/models.py`

```python
@dataclass
class Evidence:
    id: str  # NEW
    content: str
    effect: str  # "supports" | "contradicts" | "transforms"

    # Temporal
    timestamp: datetime
    session_id: str  # NEW

    # Provenance (REQUIRED)
    source_observation: str  # NEW: Link to observation ID
    reasoning: str  # NEW: Why this effect?
    confidence_before: float  # NEW
    confidence_after: float  # NEW
```

### 1.3 Update Observation Model

**Modify**: `/backend/app/chitta/models.py`

```python
@dataclass
class TemporalFact:
    id: str  # NEW: Generate on creation
    content: str
    domain: str

    # Temporal
    t_created: datetime
    session_id: str  # NEW

    # Links
    addresses_curiosity: Optional[str] = None  # NEW: If this answers a curiosity
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `curiosity_types.py` | CREATE | New type hierarchy |
| `models.py` | MODIFY | Update Evidence, TemporalFact |
| `curiosity.py` | DELETE | Replace entirely |

---

## Phase 2: Event Sourcing Infrastructure

**Goal**: Build event store for audit trails and explainability.

### 2.1 Event Models

**New file**: `/backend/app/chitta/events.py`

```python
EVENT_TYPES = [
    # Observation events
    "observation_added",

    # Curiosity lifecycle
    "curiosity_created",
    "curiosity_updated",
    "curiosity_evolved",      # Question → Hypothesis
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

@dataclass
class Change:
    field: str
    from_value: Any
    to_value: Any

@dataclass
class CuriosityEvent:
    id: str
    timestamp: datetime
    session_id: str
    child_id: str

    event_type: str
    entity_type: str  # "observation" | "curiosity" | "pattern" | "crystal"
    entity_id: str

    changes: Dict[str, Change]

    # REQUIRED Provenance
    reasoning: str
    evidence_refs: List[str]

    # Cascade tracking
    triggered_by: Optional[str] = None
    triggered_events: List[str] = field(default_factory=list)
```

### 2.2 Event Store

**New file**: `/backend/app/chitta/event_store.py`

```python
class EventStore:
    def append(self, event: CuriosityEvent) -> None:
        """Store an event."""

    def get_events_for(self, entity_id: str) -> List[CuriosityEvent]:
        """Get all events for an entity."""

    def get_events_between(self, start: datetime, end: datetime) -> List[CuriosityEvent]:
        """Get events in time range."""

    def get_events_in_session(self, session_id: str) -> List[CuriosityEvent]:
        """Get all events in a session."""

    def reconstruct_at(self, entity_id: str, timestamp: datetime) -> dict:
        """Reconstruct entity state at a point in time."""
```

### 2.3 Database Schema

**New file**: `/backend/app/db/models_events.py`

```python
class CuriosityEventDB(Base):
    __tablename__ = "curiosity_events"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    session_id = Column(String(50), nullable=False)
    child_id = Column(UUID, ForeignKey("children.id"), nullable=False)

    event_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(200), nullable=False)

    changes_json = Column(Text)
    reasoning = Column(Text, nullable=False)
    evidence_refs_json = Column(Text)

    triggered_by = Column(String, nullable=True)

    __table_args__ = (
        Index('ix_events_entity', 'entity_id'),
        Index('ix_events_session', 'session_id'),
        Index('ix_events_type', 'event_type'),
        Index('ix_events_child_time', 'child_id', 'timestamp'),
    )
```

### Files to Create

| File | Action | Description |
|------|--------|-------------|
| `events.py` | CREATE | Event models |
| `event_store.py` | CREATE | Event store interface |
| `event_recorder.py` | CREATE | Event recording service |
| `db/models_events.py` | CREATE | Database schema |
| `alembic/versions/xxx_events.py` | CREATE | Migration |

---

## Phase 3: Updated LLM Tools

**Goal**: Update tool definitions to require provenance and support new model.

### 3.1 Tool Updates

**Modify**: `/backend/app/chitta/tools.py`

#### Update TOOL_NOTICE

Add:
```python
"addresses_curiosity": {
    "type": "string",
    "description": "Focus of curiosity this observation addresses (if any)"
}
```

#### Update TOOL_WONDER

Remove `certainty`, add:
```python
"fullness_or_confidence": {
    "type": "number",
    "description": "Your assessment: 0-1"
},
"assessment_reasoning": {
    "type": "string",
    "description": "REQUIRED: Why this level?"
},
"evidence_refs": {
    "type": "array",
    "items": {"type": "string"},
    "description": "Observation IDs that inform this"
},
"emerges_from": {
    "type": "string",
    "description": "Curiosity ID this evolved from"
},
"source_hypotheses": {
    "type": "array",
    "items": {"type": "string"},
    "description": "For pattern: hypothesis IDs"
}
```

Required: `["focus", "type", "fullness_or_confidence", "assessment_reasoning"]`

#### Update TOOL_ADD_EVIDENCE

Add:
```python
"new_confidence": {"type": "number"},
"effect_reasoning": {"type": "string", "description": "REQUIRED"},
"source_observation": {"type": "string", "description": "REQUIRED"}
```

Required: `["curiosity_focus", "evidence", "effect", "effect_reasoning", "source_observation"]`

#### NEW: TOOL_SEE_PATTERN

```python
TOOL_SEE_PATTERN = {
    "name": "see_pattern",
    "description": "Record a pattern emerging across curiosities.",
    "parameters": {
        "pattern": {"type": "string"},
        "insight": {"type": "string"},
        "confidence": {"type": "number"},
        "domains_involved": {"type": "array", "items": {"type": "string"}},
        "connects": {"type": "array", "items": {"type": "string"}, "description": "REQUIRED"},
        "reasoning": {"type": "string", "description": "REQUIRED"}
    },
    "required": ["pattern", "insight", "confidence", "connects", "reasoning"]
}
```

#### NEW: TOOL_UPDATE_CURIOSITY

```python
TOOL_UPDATE_CURIOSITY = {
    "name": "update_curiosity",
    "description": "Reassess an existing curiosity.",
    "parameters": {
        "focus": {"type": "string"},
        "new_fullness_or_confidence": {"type": "number"},
        "new_pull": {"type": "number"},
        "new_status": {"type": "string", "enum": ["active", "dormant", "evolved", "refuted", "confirmed"]},
        "change_reasoning": {"type": "string", "description": "REQUIRED"},
        "triggered_by": {"type": "string", "description": "REQUIRED"}
    },
    "required": ["focus", "change_reasoning", "triggered_by"]
}
```

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `tools.py` | MODIFY | Update definitions, add new tools |
| `gestalt.py` | MODIFY | Add handlers for new tools |

---

## Phase 4: Curiosities Manager

**Goal**: New manager for type-specific curiosities.

### 4.1 Manager

**New file**: `/backend/app/chitta/curiosity_manager.py`

```python
class CuriosityManager:
    """Manages all curiosity types."""

    _discoveries: List[Discovery]
    _questions: List[Question]
    _hypotheses: List[Hypothesis]
    _patterns: List[Pattern]

    def add(self, curiosity: BaseCuriosity) -> None:
        """Route to correct type list."""

    def get_by_focus(self, focus: str) -> Optional[BaseCuriosity]:
        """Find across all types."""

    def get_by_type(self, curiosity_type: str) -> List[BaseCuriosity]:
        """Get all of specific type."""

    def get_active(self) -> List[BaseCuriosity]:
        """Get all active sorted by pull."""

    def get_lineage(self, curiosity_id: str) -> CuriosityLineage:
        """Trace evolution path."""
```

### 4.2 Decay Manager

**New file**: `/backend/app/chitta/decay.py`

```python
class DecayManager:
    """Time-based pull decay (ONLY mechanical operation system does)."""

    DECAY_RATES = {
        "discovery": 0.008,
        "question": 0.015,
        "hypothesis": 0.012,
        "pattern": 0.006,
    }

    DORMANCY_DAYS = {
        "discovery": 21,
        "question": 14,
        "hypothesis": 30,
        "pattern": 45,
    }

    def apply_decay(self, curiosity: BaseCuriosity) -> None:
        """Pull decays. Fullness/confidence do NOT."""

    def check_dormancy(self, curiosity: BaseCuriosity) -> bool:
        """Check if should become dormant."""
```

### 4.3 Cascade Handler

**New file**: `/backend/app/chitta/cascades.py`

```python
class CascadeHandler:
    def handle_refutation(self, hypothesis: Hypothesis, session_id: str) -> List[CuriosityEvent]:
        """
        When hypothesis is refuted:
        1. Reopen source question
        2. Weaken connected patterns
        3. Mark crystal for regeneration
        """

    def handle_pattern_dissolved(self, pattern: Pattern, session_id: str) -> List[CuriosityEvent]:
        """
        When pattern dissolves:
        1. Update source hypotheses
        2. Mark crystal for regeneration
        """
```

### Files to Create

| File | Action | Description |
|------|--------|-------------|
| `curiosity_manager.py` | CREATE | New manager |
| `decay.py` | CREATE | Decay logic |
| `cascades.py` | CREATE | Cascade handling |

---

## Phase 5: Crystal Versioning

**Goal**: Versioned crystals with diffs.

### 5.1 Crystal Model

**Modify**: `/backend/app/chitta/models.py`

```python
@dataclass
class CrystalDiff:
    summary: str
    narrative_changed: bool
    strengths_added: List[str]
    strengths_removed: List[str]
    edges_added: List[str]
    edges_removed: List[str]
    patterns_added: List[str]
    patterns_removed: List[str]

@dataclass
class Crystal:
    version: int
    created_at: datetime

    # Content
    narrative: str
    essence: str
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
```

### 5.2 Synthesis Updates

**Modify**: `/backend/app/chitta/synthesis.py`

- Generate diffs between versions
- Include provenance
- Record events

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `models.py` | MODIFY | CrystalDiff, Crystal updates |
| `synthesis.py` | MODIFY | Versioning and diffs |

---

## Phase 6: Gestalt Integration

**Goal**: Wire everything together in Darshan.

### 6.1 Update Gestalt

**Modify**: `/backend/app/chitta/gestalt.py`

- Replace `Curiosities` with `CuriosityManager`
- Add `EventRecorder` integration
- Add `DecayManager` integration
- Add `CascadeHandler` integration
- Update tool handlers for new models

### 6.2 Update Formatting

**Modify**: `/backend/app/chitta/formatting.py`

- Format new curiosity types for LLM prompt
- Show fullness/confidence appropriately
- Include provenance in context

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `gestalt.py` | MODIFY | Major refactor |
| `formatting.py` | MODIFY | New type formatting |

---

## Execution Order

```
Phase 1: Core Data Models ────────────┐
                                       ├── Can run in parallel
Phase 2: Event Sourcing ──────────────┘
          │
          ↓
Phase 3: LLM Tools ─────────────────────
          │
          ↓
Phase 4: Curiosities Manager ───────────
          │
          ↓
Phase 5: Crystal Versioning ────────────
          │
          ↓
Phase 6: Gestalt Integration ───────────
```

---

## Testing Strategy

### Per Phase

| Phase | Tests |
|-------|-------|
| 1 | Model serialization, type behavior |
| 2 | Event recording, retrieval, reconstruction |
| 3 | Tool validation, required fields |
| 4 | Manager operations, decay, cascades |
| 5 | Crystal versioning, diff generation |
| 6 | Integration tests, full flow |

---

## Success Criteria

- [ ] All curiosities have correct type (Discovery/Question/Hypothesis/Pattern)
- [ ] Receptive use `fullness`, Assertive use `confidence`
- [ ] All state changes recorded as events with reasoning
- [ ] Crystals are versioned with diffs
- [ ] Lineage trackable for any curiosity
- [ ] All tests pass
- [ ] Dashboard displays new structure correctly
