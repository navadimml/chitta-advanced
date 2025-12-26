"""
Curiosity Events - Event Sourcing for Audit & Explainability

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module implements event sourcing for the curiosity system.
Every state change is recorded as an immutable event with full provenance.

WHY EVENT SOURCING:
1. Audit Trail: Regulatory compliance (GDPR, HIPAA, AI regulations)
2. Explainability: "Why did the system conclude X?"
3. Temporal Queries: "What did we understand at age 3?"
4. Debugging: Full replay of state evolution

DESIGN PRINCIPLES:
- Events are immutable records of what happened
- Every event has required reasoning and evidence refs
- Cascade tracking shows cause-effect relationships
- System ONLY records events, NEVER makes semantic decisions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import uuid
import json


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return f"evt_{uuid.uuid4().hex[:12]}"


# =============================================================================
# Event Types
# =============================================================================

# Observation events
OBSERVATION_ADDED = "observation_added"

# Curiosity lifecycle events
CURIOSITY_CREATED = "curiosity_created"
CURIOSITY_UPDATED = "curiosity_updated"
CURIOSITY_EVOLVED = "curiosity_evolved"  # Question → Hypothesis
CURIOSITY_DORMANT = "curiosity_dormant"
CURIOSITY_REVIVED = "curiosity_revived"
CURIOSITY_REFUTED = "curiosity_refuted"
CURIOSITY_TRANSFORMED = "curiosity_transformed"

# Evidence events
EVIDENCE_ADDED = "evidence_added"

# Pattern events
PATTERN_EMERGED = "pattern_emerged"
PATTERN_STRENGTHENED = "pattern_strengthened"
PATTERN_QUESTIONED = "pattern_questioned"
PATTERN_DISSOLVED = "pattern_dissolved"

# Crystal events
CRYSTAL_SYNTHESIZED = "crystal_synthesized"
CRYSTAL_UPDATED = "crystal_updated"

# All valid event types
EVENT_TYPES = {
    # Observation
    OBSERVATION_ADDED,
    # Curiosity lifecycle
    CURIOSITY_CREATED,
    CURIOSITY_UPDATED,
    CURIOSITY_EVOLVED,
    CURIOSITY_DORMANT,
    CURIOSITY_REVIVED,
    CURIOSITY_REFUTED,
    CURIOSITY_TRANSFORMED,
    # Evidence
    EVIDENCE_ADDED,
    # Pattern
    PATTERN_EMERGED,
    PATTERN_STRENGTHENED,
    PATTERN_QUESTIONED,
    PATTERN_DISSOLVED,
    # Crystal
    CRYSTAL_SYNTHESIZED,
    CRYSTAL_UPDATED,
}

# Entity types
ENTITY_OBSERVATION = "observation"
ENTITY_CURIOSITY = "curiosity"
ENTITY_PATTERN = "pattern"
ENTITY_CRYSTAL = "crystal"
ENTITY_EVIDENCE = "evidence"

ENTITY_TYPES = {
    ENTITY_OBSERVATION,
    ENTITY_CURIOSITY,
    ENTITY_PATTERN,
    ENTITY_CRYSTAL,
    ENTITY_EVIDENCE,
}


# =============================================================================
# Change Tracking
# =============================================================================

@dataclass
class Change:
    """
    A single field change within an event.

    Records what field changed, from what value, to what value.
    Used for state reconstruction and diff viewing.
    """
    field: str
    from_value: Any
    to_value: Any

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "from": self.from_value,
            "to": self.to_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Change":
        return cls(
            field=data["field"],
            from_value=data.get("from"),
            to_value=data.get("to"),
        )


# =============================================================================
# Core Event Model
# =============================================================================

@dataclass
class CuriosityEvent:
    """
    An immutable record of a state change in the curiosity system.

    Every event captures:
    - WHAT changed (entity_type, entity_id, changes)
    - WHEN it changed (timestamp)
    - WHERE in the session (session_id, child_id)
    - WHY it changed (reasoning, evidence_refs) - REQUIRED
    - WHAT triggered it (triggered_by, triggered_events)

    Events form a directed graph through triggered_by/triggered_events,
    enabling cascade tracking and root cause analysis.
    """
    id: str
    timestamp: datetime
    session_id: str
    child_id: str

    # What happened
    event_type: str  # One of EVENT_TYPES
    entity_type: str  # One of ENTITY_TYPES
    entity_id: str  # ID of the affected entity

    # What changed
    changes: Dict[str, Change]  # field_name -> Change

    # REQUIRED Provenance - for explainability
    reasoning: str  # Why did this change happen?
    evidence_refs: List[str]  # Observation/evidence IDs that support this

    # Cascade tracking
    triggered_by: Optional[str] = None  # Parent event ID
    triggered_events: List[str] = field(default_factory=list)  # Child event IDs

    def __post_init__(self):
        """Validate event after creation."""
        if self.event_type not in EVENT_TYPES:
            raise ValueError(f"Invalid event_type: {self.event_type}")
        if self.entity_type not in ENTITY_TYPES:
            raise ValueError(f"Invalid entity_type: {self.entity_type}")
        if not self.reasoning:
            raise ValueError("Event reasoning is required")

    @classmethod
    def create(
        cls,
        event_type: str,
        entity_type: str,
        entity_id: str,
        changes: Dict[str, Change],
        reasoning: str,
        evidence_refs: List[str],
        session_id: str,
        child_id: str,
        triggered_by: Optional[str] = None,
    ) -> "CuriosityEvent":
        """Create a new event with generated ID and current timestamp."""
        return cls(
            id=generate_event_id(),
            timestamp=datetime.now(),
            session_id=session_id,
            child_id=child_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            triggered_by=triggered_by,
        )

    def add_triggered_event(self, event_id: str):
        """Record that this event triggered another event."""
        if event_id not in self.triggered_events:
            self.triggered_events.append(event_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for persistence."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "child_id": self.child_id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "changes": {k: v.to_dict() for k, v in self.changes.items()},
            "reasoning": self.reasoning,
            "evidence_refs": self.evidence_refs,
            "triggered_by": self.triggered_by,
            "triggered_events": self.triggered_events,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CuriosityEvent":
        """Deserialize from dict."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        else:
            timestamp = timestamp or datetime.now()

        changes = {}
        for k, v in data.get("changes", {}).items():
            if isinstance(v, dict):
                changes[k] = Change.from_dict(v)
            else:
                # Handle legacy format
                changes[k] = Change(field=k, from_value=None, to_value=v)

        return cls(
            id=data["id"],
            timestamp=timestamp,
            session_id=data.get("session_id", ""),
            child_id=data.get("child_id", ""),
            event_type=data["event_type"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            changes=changes,
            reasoning=data.get("reasoning", ""),
            evidence_refs=data.get("evidence_refs", []),
            triggered_by=data.get("triggered_by"),
            triggered_events=data.get("triggered_events", []),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CuriosityEvent":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


# =============================================================================
# Event Builders (Convenience Functions)
# =============================================================================

def build_observation_added_event(
    observation_id: str,
    content: str,
    domain: str,
    session_id: str,
    child_id: str,
    addresses_curiosity: Optional[str] = None,
) -> CuriosityEvent:
    """Build an observation_added event."""
    changes = {
        "content": Change("content", None, content),
        "domain": Change("domain", None, domain),
    }
    if addresses_curiosity:
        changes["addresses_curiosity"] = Change("addresses_curiosity", None, addresses_curiosity)

    return CuriosityEvent.create(
        event_type=OBSERVATION_ADDED,
        entity_type=ENTITY_OBSERVATION,
        entity_id=observation_id,
        changes=changes,
        reasoning=f"Observation recorded: {content[:50]}...",
        evidence_refs=[],
        session_id=session_id,
        child_id=child_id,
    )


def build_curiosity_created_event(
    curiosity_id: str,
    curiosity_type: str,
    focus: str,
    domain: str,
    initial_value: float,  # fullness or confidence
    reasoning: str,
    evidence_refs: List[str],
    session_id: str,
    child_id: str,
    emerges_from: Optional[str] = None,
) -> CuriosityEvent:
    """Build a curiosity_created event."""
    metric_name = "fullness" if curiosity_type in ("discovery", "question") else "confidence"
    changes = {
        "type": Change("type", None, curiosity_type),
        "focus": Change("focus", None, focus),
        "domain": Change("domain", None, domain),
        metric_name: Change(metric_name, None, initial_value),
        "status": Change("status", None, "sparse" if curiosity_type == "discovery" else "open" if curiosity_type == "question" else "weak" if curiosity_type == "hypothesis" else "emerging"),
    }
    if emerges_from:
        changes["emerges_from"] = Change("emerges_from", None, emerges_from)

    return CuriosityEvent.create(
        event_type=CURIOSITY_CREATED,
        entity_type=ENTITY_CURIOSITY,
        entity_id=curiosity_id,
        changes=changes,
        reasoning=reasoning,
        evidence_refs=evidence_refs,
        session_id=session_id,
        child_id=child_id,
    )


def build_curiosity_updated_event(
    curiosity_id: str,
    changes: Dict[str, Change],
    reasoning: str,
    evidence_refs: List[str],
    session_id: str,
    child_id: str,
    triggered_by: Optional[str] = None,
) -> CuriosityEvent:
    """Build a curiosity_updated event."""
    return CuriosityEvent.create(
        event_type=CURIOSITY_UPDATED,
        entity_type=ENTITY_CURIOSITY,
        entity_id=curiosity_id,
        changes=changes,
        reasoning=reasoning,
        evidence_refs=evidence_refs,
        session_id=session_id,
        child_id=child_id,
        triggered_by=triggered_by,
    )


def build_evidence_added_event(
    evidence_id: str,
    curiosity_id: str,
    content: str,
    effect: str,
    confidence_before: float,
    confidence_after: float,
    reasoning: str,
    source_observation: str,
    session_id: str,
    child_id: str,
) -> CuriosityEvent:
    """Build an evidence_added event."""
    changes = {
        "content": Change("content", None, content),
        "effect": Change("effect", None, effect),
        "confidence": Change("confidence", confidence_before, confidence_after),
        "source_observation": Change("source_observation", None, source_observation),
    }

    return CuriosityEvent.create(
        event_type=EVIDENCE_ADDED,
        entity_type=ENTITY_EVIDENCE,
        entity_id=evidence_id,
        changes=changes,
        reasoning=reasoning,
        evidence_refs=[source_observation],
        session_id=session_id,
        child_id=child_id,
    )


def build_curiosity_evolved_event(
    source_curiosity_id: str,
    target_curiosity_id: str,
    reasoning: str,
    evidence_refs: List[str],
    session_id: str,
    child_id: str,
) -> CuriosityEvent:
    """Build a curiosity_evolved event (Question → Hypothesis)."""
    changes = {
        "status": Change("status", "answered", "evolved"),
        "spawned_hypothesis": Change("spawned_hypothesis", None, target_curiosity_id),
    }

    return CuriosityEvent.create(
        event_type=CURIOSITY_EVOLVED,
        entity_type=ENTITY_CURIOSITY,
        entity_id=source_curiosity_id,
        changes=changes,
        reasoning=reasoning,
        evidence_refs=evidence_refs,
        session_id=session_id,
        child_id=child_id,
    )


def build_curiosity_refuted_event(
    curiosity_id: str,
    reasoning: str,
    evidence_refs: List[str],
    session_id: str,
    child_id: str,
    triggered_by: Optional[str] = None,
) -> CuriosityEvent:
    """Build a curiosity_refuted event."""
    changes = {
        "status": Change("status", "testing", "refuted"),
    }

    return CuriosityEvent.create(
        event_type=CURIOSITY_REFUTED,
        entity_type=ENTITY_CURIOSITY,
        entity_id=curiosity_id,
        changes=changes,
        reasoning=reasoning,
        evidence_refs=evidence_refs,
        session_id=session_id,
        child_id=child_id,
        triggered_by=triggered_by,
    )


def build_pattern_emerged_event(
    pattern_id: str,
    focus: str,
    insight: str,
    domains_involved: List[str],
    source_hypotheses: List[str],
    confidence: float,
    reasoning: str,
    session_id: str,
    child_id: str,
) -> CuriosityEvent:
    """Build a pattern_emerged event."""
    changes = {
        "focus": Change("focus", None, focus),
        "insight": Change("insight", None, insight),
        "domains_involved": Change("domains_involved", None, domains_involved),
        "source_hypotheses": Change("source_hypotheses", None, source_hypotheses),
        "confidence": Change("confidence", None, confidence),
        "status": Change("status", None, "emerging"),
    }

    return CuriosityEvent.create(
        event_type=PATTERN_EMERGED,
        entity_type=ENTITY_PATTERN,
        entity_id=pattern_id,
        changes=changes,
        reasoning=reasoning,
        evidence_refs=source_hypotheses,
        session_id=session_id,
        child_id=child_id,
    )


def build_crystal_synthesized_event(
    crystal_version: int,
    source_observations: List[str],
    source_patterns: List[str],
    reasoning: str,
    session_id: str,
    child_id: str,
) -> CuriosityEvent:
    """Build a crystal_synthesized event."""
    changes = {
        "version": Change("version", crystal_version - 1 if crystal_version > 1 else None, crystal_version),
        "source_observations": Change("source_observations", None, source_observations),
        "source_patterns": Change("source_patterns", None, source_patterns),
    }

    return CuriosityEvent.create(
        event_type=CRYSTAL_SYNTHESIZED,
        entity_type=ENTITY_CRYSTAL,
        entity_id=f"crystal_v{crystal_version}",
        changes=changes,
        reasoning=reasoning,
        evidence_refs=source_observations + source_patterns,
        session_id=session_id,
        child_id=child_id,
    )


# =============================================================================
# Event Summary (for display)
# =============================================================================

@dataclass
class EventSummary:
    """
    Human-readable summary of an event.

    Used for dashboard display and debugging.
    """
    event_id: str
    timestamp: datetime
    event_type: str
    entity_type: str
    entity_id: str
    summary_text: str  # Human-readable summary
    has_cascade: bool  # Did this trigger other events?

    @classmethod
    def from_event(cls, event: CuriosityEvent) -> "EventSummary":
        """Create summary from event."""
        # Generate human-readable summary
        if event.event_type == OBSERVATION_ADDED:
            content = event.changes.get("content")
            summary = f"Observation: {content.to_value[:40]}..." if content else "Observation added"
        elif event.event_type == CURIOSITY_CREATED:
            focus = event.changes.get("focus")
            ctype = event.changes.get("type")
            summary = f"New {ctype.to_value if ctype else 'curiosity'}: {focus.to_value if focus else '?'}"
        elif event.event_type == CURIOSITY_UPDATED:
            summary = f"Updated curiosity: {event.entity_id}"
        elif event.event_type == EVIDENCE_ADDED:
            effect = event.changes.get("effect")
            summary = f"Evidence ({effect.to_value if effect else '?'}) added"
        elif event.event_type == CURIOSITY_EVOLVED:
            summary = f"Question evolved to hypothesis"
        elif event.event_type == CURIOSITY_REFUTED:
            summary = f"Hypothesis refuted"
        elif event.event_type == PATTERN_EMERGED:
            focus = event.changes.get("focus")
            summary = f"Pattern emerged: {focus.to_value if focus else '?'}"
        elif event.event_type == CRYSTAL_SYNTHESIZED:
            version = event.changes.get("version")
            summary = f"Crystal synthesized (v{version.to_value if version else '?'})"
        else:
            summary = f"{event.event_type}: {event.entity_id}"

        return cls(
            event_id=event.id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            summary_text=summary,
            has_cascade=len(event.triggered_events) > 0,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "summary_text": self.summary_text,
            "has_cascade": self.has_cascade,
        }
