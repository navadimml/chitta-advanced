"""
Developmental Understanding Models

The hypothesis-driven model for tracking a child's developmental journey.
Everything is a hypothesis - held lightly, updated with evidence.

Core philosophy:
- Evidence is immutable, timestamped
- Hypotheses evolve with evidence
- Patterns emerge across hypotheses
- Insights come from reflection
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


class Evidence(BaseModel):
    """
    A single piece of evidence - immutable, timestamped.

    Evidence is a moment in time. It doesn't change.
    "In November, parent said transitions were hard" is always true.
    """
    id: str = Field(default_factory=generate_id)
    observed_at: datetime = Field(default_factory=datetime.now)
    source: str  # "conversation", "video", "parent_update"
    content: str  # What was observed/said
    domain: Optional[str] = None  # "motor", "social", "transitions"


class Hypothesis(BaseModel):
    """
    An evolving understanding about the child.

    A hypothesis is not a diagnosis - it's a working theory.
    It strengthens or weakens with evidence.
    It can be resolved: confirmed, refuted, evolved, or outgrown.

    The evidence list IS the journey - chronological story of how
    our understanding developed.
    """
    id: str = Field(default_factory=generate_id)
    theory: str  # "Maya struggles with transitions"
    domain: str  # "regulation", "motor", "social", "communication"

    # Where this hypothesis came from
    source: str = "observation"  # "observation", "pattern", "domain_knowledge", "contradiction"
    source_details: Optional[str] = None  # "Parent mentioned noise AND textures AND transitions"

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
    Emergent theme across multiple hypotheses.

    Patterns are detected by reflection - connecting dots across hypotheses.
    "Sensory processing seems involved" links motor + transitions + food textures.
    """
    id: str = Field(default_factory=generate_id)
    theme: str  # "sensory processing involvement"
    description: str  # Longer explanation
    related_hypotheses: List[str] = Field(default_factory=list)  # hypothesis IDs
    confidence: float = 0.5
    detected_at: datetime = Field(default_factory=datetime.now)
    source: str = "reflection"  # "domain_knowledge", "reflection", "explicit"


class PendingInsight(BaseModel):
    """
    Insight from reflection, to be shared naturally in conversation.

    Reflection happens in background. Insights queue up to be shared
    when contextually appropriate.
    """
    id: str = Field(default_factory=generate_id)
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
