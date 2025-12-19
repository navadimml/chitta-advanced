"""
Developmental Understanding Models

TEMPORAL DESIGN (see docs/TEMPORAL_DESIGN.md):
- Hypotheses are now OWNED BY ExplorationCycles (not here)
- Patterns remain here as cross-cycle observations
- PendingInsights for sharing discoveries naturally

What lives here:
- Pattern: Cross-cycle observations ("motor concerns appear during transitions")
- PendingInsight: Queued insights to share with parent
- DevelopmentalUnderstanding: Container for patterns and insights

What moved to exploration.py:
- Evidence: Now in exploration.py, owned by cycles
- Hypothesis: Now in exploration.py, owned by cycles
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


# === DEPRECATED: Evidence and Hypothesis moved to exploration.py ===
# These are kept here for backward compatibility during migration.
# New code should use the versions from exploration.py

class Evidence(BaseModel):
    """
    DEPRECATED: Use Evidence from exploration.py instead.
    Kept for backward compatibility.
    """
    id: str = Field(default_factory=generate_id)
    observed_at: datetime = Field(default_factory=datetime.now)
    source: str  # "conversation", "video", "parent_update"
    content: str  # What was observed/said
    domain: Optional[str] = None  # "motor", "social", "transitions"


class Hypothesis(BaseModel):
    """
    DEPRECATED: Use Hypothesis from exploration.py instead.

    Hypotheses should now be owned by ExplorationCycles.
    This class is kept for backward compatibility.
    """
    id: str = Field(default_factory=generate_id)
    theory: str  # "Maya struggles with transitions"
    domain: str  # "regulation", "motor", "social", "communication"

    # Where this hypothesis came from
    source: str = "observation"  # "observation", "pattern", "domain_knowledge", "contradiction"
    source_details: Optional[str] = None  # "Parent mentioned noise AND textures AND transitions"

    # Questions that would test this hypothesis
    questions_to_explore: List[str] = Field(default_factory=list)

    # Evidence chain - the journey
    evidence: List[Evidence] = Field(default_factory=list)

    # Current state
    status: str = "forming"  # "forming", "active", "weakening", "resolved"
    confidence: float = 0.5  # 0-1, changes with evidence

    # Timestamps
    formed_at: datetime = Field(default_factory=datetime.now)
    last_evidence_at: datetime = Field(default_factory=datetime.now)

    # Resolution (when status = "resolved")
    resolution: Optional[str] = None  # "confirmed", "refuted", "evolved", "outgrown"
    resolution_note: Optional[str] = None  # "Improved with OT", "Was developmental phase"
    evolved_into: Optional[str] = None  # New hypothesis ID if evolved

    def add_evidence(self, evidence: Evidence, effect: str = "neutral"):
        """
        Add evidence and update state.

        effect: "supports", "contradicts", "neutral", "transforms"
        """
        self.evidence.append(evidence)
        self.last_evidence_at = evidence.observed_at

        if effect == "supports":
            self.confidence = min(1.0, self.confidence + 0.15)
            if self.status == "forming" and self.confidence > 0.6:
                self.status = "active"

        elif effect == "contradicts":
            self.confidence = max(0.0, self.confidence - 0.2)
            if self.confidence < 0.3:
                self.status = "weakening"

        elif effect == "transforms":
            self.status = "evolving"

    def resolve(self, resolution: str, note: Optional[str] = None, evolved_into: Optional[str] = None):
        """Mark hypothesis as resolved."""
        self.status = "resolved"
        self.resolution = resolution
        self.resolution_note = note
        self.evolved_into = evolved_into

    def is_stale(self, days: int = 90) -> bool:
        """Check if hypothesis hasn't had evidence in a while."""
        cutoff = datetime.now() - timedelta(days=days)
        return self.last_evidence_at < cutoff and self.status in ["forming", "active"]


class Pattern(BaseModel):
    """
    Emergent theme across multiple cycles - a CROSS-CYCLE observation.

    Patterns connect dots ACROSS cycles over time.
    "Motor concerns appear during life transitions" links cycles 1, 5, 8.

    Unlike hypotheses (which are cycle-owned), patterns are observations
    ABOUT the journey across cycles.
    """
    id: str = Field(default_factory=generate_id)
    theme: str  # "sensory processing involvement"
    description: str  # Longer explanation

    # Cross-cycle references (the primary model now)
    supporting_cycle_ids: List[str] = Field(default_factory=list)

    # DEPRECATED: Use supporting_cycle_ids instead
    related_hypotheses: List[str] = Field(default_factory=list)

    confidence: float = 0.5
    detected_at: datetime = Field(default_factory=datetime.now)
    source: str = "reflection"  # "domain_knowledge", "reflection", "explicit"


# === Synthesis Report (Cross-Cycle) ===

class CycleSnapshot(BaseModel):
    """Snapshot of a cycle's state at the time of synthesis."""
    cycle_id: str
    focus: Optional[str] = None
    domain: Optional[str] = None
    status: str  # "complete", "active", "evidence_gathering"
    key_findings: List[str] = Field(default_factory=list)
    hypothesis_count: int = 0


class SynthesisReport(BaseModel):
    """
    Cross-cycle synthesis - the longitudinal story.

    Unlike cycle artifacts (owned by one cycle), synthesis reports
    are owned by the Child and span multiple cycles.

    A synthesis tells the narrative of development over time,
    not just what's happening now.
    """
    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=datetime.now)

    # What this report covers
    cycle_ids: List[str] = Field(default_factory=list)
    time_span_start: Optional[datetime] = None
    time_span_end: Optional[datetime] = None

    # Snapshots of each cycle's state at report time
    cycle_snapshots: List[CycleSnapshot] = Field(default_factory=list)

    # The actual content
    narrative: Optional[str] = None  # The story
    key_developments: List[str] = Field(default_factory=list)
    current_focus: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)

    # Metadata
    audience: str = "parent"  # "parent", "clinician"
    triggered_by: str = "user_request"  # "scheduled", "milestone", "user_request"

    # Report format/content
    content: Dict[str, Any] = Field(default_factory=dict)


class PendingInsight(BaseModel):
    """
    Insight from reflection, to be shared naturally in conversation.

    Reflection happens in background. Insights queue up to be shared
    when contextually appropriate.
    """
    id: str = Field(default_factory=generate_id)
    source: str = "reflection"  # "reflection", "parent_goal", "urgent_flag", "observation"
    content: str  # "I noticed noise and transitions might be connected"
    importance: str = "medium"  # "low", "medium", "high"
    share_when: str = "when_relevant"  # "next_turn", "when_relevant", "when_asked"
    related_hypotheses: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    shared: bool = False

    def mark_shared(self):
        self.shared = True


class DevelopmentalUnderstanding(BaseModel):
    """
    Our evolving understanding of this child.

    This is the living, breathing model of what we know.
    It's never "complete" - always growing, always updating.
    """
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    patterns: List[Pattern] = Field(default_factory=list)
    pending_insights: List[PendingInsight] = Field(default_factory=list)

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        return next((h for h in self.hypotheses if h.id == hypothesis_id), None)

    def active_hypotheses(self) -> List[Hypothesis]:
        """Hypotheses we're actively exploring."""
        return [h for h in self.hypotheses if h.status in ["forming", "active"]]

    def stale_hypotheses(self, days: int = 90) -> List[Hypothesis]:
        """Hypotheses that haven't had evidence in a while."""
        return [h for h in self.active_hypotheses() if h.is_stale(days)]

    def hypotheses_for_domain(self, domain: str) -> List[Hypothesis]:
        """All hypotheses for a domain, any status."""
        return [h for h in self.hypotheses if h.domain == domain]

    def journey_for_domain(self, domain: str) -> List[Evidence]:
        """Chronological evidence chain for a domain - the story."""
        relevant = self.hypotheses_for_domain(domain)
        all_evidence = []
        for h in relevant:
            all_evidence.extend(h.evidence)
        return sorted(all_evidence, key=lambda e: e.observed_at)

    def unshared_insights(self) -> List[PendingInsight]:
        """Insights ready to share."""
        return [i for i in self.pending_insights if not i.shared]

    def add_hypothesis(self, hypothesis: Hypothesis):
        self.hypotheses.append(hypothesis)

    def add_pattern(self, pattern: Pattern):
        self.patterns.append(pattern)

    def add_insight(self, insight: PendingInsight):
        self.pending_insights.append(insight)
