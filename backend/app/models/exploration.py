"""
Exploration Cycle Models

TEMPORAL DESIGN (see docs/TEMPORAL_DESIGN.md):
- Cycles are time-bounded containers for focused exploration
- Hypotheses are OWNED by cycles, frozen when cycle completes
- Multiple cycles can run in parallel (asynchronous)
- Conversation is never blocked by a cycle
- Completed cycles are immutable historical records

Cycle lifecycle:
- active: Building understanding through conversation
- evidence_gathering: Have guidelines, waiting for videos
- synthesizing: Videos uploaded, analyzing and creating report
- complete: Done (frozen - hypotheses and evidence immutable)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


# === Evidence & Hypothesis (Cycle-Owned) ===

class Evidence(BaseModel):
    """
    A single piece of evidence - immutable, timestamped.

    Evidence is a moment in time. It doesn't change.
    "In November, parent said transitions were hard" is always true.

    Evidence can belong to one or more cycles (cross-cycle evidence).
    """
    id: str = Field(default_factory=generate_id)
    observed_at: datetime = Field(default_factory=datetime.now)
    source: str  # "conversation", "video", "parent_update"
    content: str  # What was observed/said
    domain: Optional[str] = None  # "motor", "social", "transitions"

    # Cross-cycle support: evidence can inform multiple cycles
    applies_to_cycle_ids: List[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    """
    A theory about what's happening NOW - owned by its cycle.

    When a cycle completes, its hypotheses are frozen.
    If concerns return later, a NEW hypothesis is created in a NEW cycle.

    This preserves the temporal narrative - what we understood THEN
    vs what we understand NOW.
    """
    id: str = Field(default_factory=generate_id)
    theory: str  # "Maya struggles with transitions"
    domain: str  # "regulation", "motor", "social", "communication"

    # Where this hypothesis came from
    source: str = "observation"  # "observation", "pattern", "domain_knowledge", "contradiction"
    source_details: Optional[str] = None

    # Questions that would test this hypothesis
    questions_to_explore: List[str] = Field(default_factory=list)

    # Evidence chain - the journey within this cycle
    evidence: List[Evidence] = Field(default_factory=list)

    # Current state (mutable while cycle active, frozen when complete)
    status: str = "forming"  # "forming", "active", "weakening", "resolved"
    confidence: float = 0.5  # 0-1, changes with evidence

    # Timestamps
    formed_at: datetime = Field(default_factory=datetime.now)
    last_evidence_at: datetime = Field(default_factory=datetime.now)

    # Resolution (when status = "resolved")
    resolution: Optional[str] = None  # "confirmed", "refuted", "evolved", "outgrown"
    resolution_note: Optional[str] = None

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

    def resolve(self, resolution: str, note: Optional[str] = None):
        """Mark hypothesis as resolved."""
        self.status = "resolved"
        self.resolution = resolution
        self.resolution_note = note

    def is_stale(self, days: int = 90) -> bool:
        """Check if hypothesis hasn't had evidence in a while."""
        cutoff = datetime.now() - timedelta(days=days)
        return self.last_evidence_at < cutoff and self.status in ["forming", "active"]


class CycleArtifact(BaseModel):
    """
    Artifact produced within an exploration cycle.

    Artifacts are tied to cycles and hypotheses.
    They have lifecycle states that drive card visibility.
    """
    id: str = Field(default_factory=generate_id)
    type: str  # "video_guidelines", "video_analysis", "synthesis_report"
    content: Dict[str, Any] = Field(default_factory=dict)
    content_format: str = "json"  # "json", "text", "markdown"

    # State - drives card visibility
    status: str = "draft"  # "draft", "ready", "fulfilled", "superseded", "needs_update"

    # What hypotheses this artifact explores
    related_hypothesis_ids: List[str] = Field(default_factory=list)

    # Fulfillment tracking (for guidelines)
    expected_videos: int = 0
    uploaded_videos: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    ready_at: Optional[datetime] = None

    # Staleness tracking
    superseded_by: Optional[str] = None  # New artifact ID if replaced
    superseded_reason: Optional[str] = None

    def mark_ready(self):
        self.status = "ready"
        self.ready_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_fulfilled(self):
        self.status = "fulfilled"
        self.updated_at = datetime.now()

    def mark_superseded(self, reason: str, new_artifact_id: Optional[str] = None):
        self.status = "superseded"
        self.superseded_reason = reason
        self.superseded_by = new_artifact_id
        self.updated_at = datetime.now()

    def mark_needs_update(self):
        self.status = "needs_update"
        self.updated_at = datetime.now()

    def add_video(self):
        """Track video upload for guidelines."""
        self.uploaded_videos += 1
        self.updated_at = datetime.now()
        if self.uploaded_videos >= self.expected_videos:
            self.mark_fulfilled()

    @property
    def videos_remaining(self) -> int:
        return max(0, self.expected_videos - self.uploaded_videos)

    @property
    def is_actionable(self) -> bool:
        """Is this artifact in a state that should show a card?"""
        return self.status in ["ready", "needs_update"]


class ConversationQuestion(BaseModel):
    """A question explored through conversation."""
    question: str
    asked_at: Optional[datetime] = None
    response_summary: Optional[str] = None
    answered: bool = False


class VideoScenario(BaseModel):
    """A video scenario for exploration."""
    id: str = Field(default_factory=generate_id)
    title: str
    what_to_film: str
    target_hypothesis: str  # What we're testing
    what_we_hope_to_learn: str
    focus_points: List[str] = Field(default_factory=list)  # Internal analysis points
    uploaded: bool = False
    video_id: Optional[str] = None  # Reference to uploaded video


class ConversationMethod(BaseModel):
    """Conversation-based exploration method."""
    questions: List[ConversationQuestion] = Field(default_factory=list)

    def add_question(self, question: str):
        self.questions.append(ConversationQuestion(question=question))

    def answered_count(self) -> int:
        return len([q for q in self.questions if q.answered])


class VideoMethod(BaseModel):
    """Video-based exploration method."""
    scenarios: List[VideoScenario] = Field(default_factory=list)

    def add_scenario(self, scenario: VideoScenario):
        self.scenarios.append(scenario)

    def uploaded_count(self) -> int:
        return len([s for s in self.scenarios if s.uploaded])

    def mark_uploaded(self, scenario_id: str, video_id: str):
        for s in self.scenarios:
            if s.id == scenario_id:
                s.uploaded = True
                s.video_id = video_id
                break


class ExplorationCycle(BaseModel):
    """
    A cycle of exploration - a time-bounded container.

    TEMPORAL DESIGN:
    - Cycles OWN their hypotheses (not just reference IDs)
    - Multiple cycles can run in parallel (asynchronous)
    - When a cycle completes, all data is frozen/immutable
    - Conversation is never blocked by a cycle's state

    A cycle has a clear focus (hypotheses), uses various methods
    (conversation, video), and produces artifacts along the way.
    """
    id: str = Field(default_factory=generate_id)

    # What we're exploring - hypotheses are OWNED by this cycle
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    focus_description: Optional[str] = None  # "Exploring motor concerns and transitions"
    focus_domain: Optional[str] = None  # Primary domain: "motor", "social", "speech", etc.

    # DEPRECATED: Use hypotheses list directly
    # Kept for backward compatibility during migration
    hypothesis_ids: List[str] = Field(default_factory=list)

    # Lifecycle
    status: str = "active"  # "active", "evidence_gathering", "synthesizing", "complete"

    # Methods used in this cycle
    conversation_method: Optional[ConversationMethod] = None
    video_method: Optional[VideoMethod] = None

    # Artifacts produced
    artifacts: List[CycleArtifact] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def get_artifact(self, artifact_type: str) -> Optional[CycleArtifact]:
        """Get artifact by type."""
        return next((a for a in self.artifacts if a.type == artifact_type), None)

    def active_artifacts(self) -> List[CycleArtifact]:
        """Artifacts in actionable state."""
        return [a for a in self.artifacts if a.is_actionable]

    def add_artifact(self, artifact: CycleArtifact):
        self.artifacts.append(artifact)
        self.updated_at = datetime.now()

    def transition_to(self, new_status: str):
        """Transition cycle to new status."""
        self.status = new_status
        self.updated_at = datetime.now()
        if new_status == "complete":
            self.completed_at = datetime.now()

    def start_video_exploration(self, scenarios: List[VideoScenario]):
        """Initialize video method and transition to evidence gathering."""
        self.video_method = VideoMethod(scenarios=scenarios)
        self.transition_to("evidence_gathering")

    def start_conversation_exploration(self, questions: List[str]):
        """Initialize conversation method."""
        self.conversation_method = ConversationMethod()
        for q in questions:
            self.conversation_method.add_question(q)

    @property
    def is_active(self) -> bool:
        return self.status != "complete"

    @property
    def has_pending_videos(self) -> bool:
        if not self.video_method:
            return False
        guidelines = self.get_artifact("video_guidelines")
        if not guidelines:
            return False
        return guidelines.videos_remaining > 0

    # === Hypothesis Management ===

    def add_hypothesis(self, hypothesis: Hypothesis):
        """Add a hypothesis to this cycle."""
        self.hypotheses.append(hypothesis)
        # Also maintain backward-compat hypothesis_ids list
        self.hypothesis_ids.append(hypothesis.id)
        self.updated_at = datetime.now()

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get hypothesis by ID."""
        return next((h for h in self.hypotheses if h.id == hypothesis_id), None)

    def active_hypotheses(self) -> List[Hypothesis]:
        """Hypotheses that are still being explored."""
        return [h for h in self.hypotheses if h.status in ["forming", "active"]]

    def resolved_hypotheses(self) -> List[Hypothesis]:
        """Hypotheses that have been resolved."""
        return [h for h in self.hypotheses if h.status == "resolved"]

    def hypotheses_for_domain(self, domain: str) -> List[Hypothesis]:
        """All hypotheses for a specific domain."""
        return [h for h in self.hypotheses if h.domain == domain]

    def add_evidence_to_hypothesis(
        self,
        hypothesis_id: str,
        evidence: Evidence,
        effect: str = "neutral"
    ):
        """Add evidence to a specific hypothesis."""
        hypothesis = self.get_hypothesis(hypothesis_id)
        if hypothesis:
            hypothesis.add_evidence(evidence, effect)
            self.updated_at = datetime.now()

    @property
    def domains(self) -> List[str]:
        """All domains covered by this cycle's hypotheses."""
        return list(set(h.domain for h in self.hypotheses))


def check_artifact_staleness(
    cycle: ExplorationCycle,
    hypotheses: dict,  # {id: Hypothesis}
    threshold_changes: int = 2
) -> None:
    """
    Check if cycle's artifacts need updating based on hypothesis changes.

    Called by reflection worker after processing.
    """
    guidelines = cycle.get_artifact("video_guidelines")

    if not guidelines or guidelines.status in ["fulfilled", "superseded"]:
        return

    # Check if related hypotheses changed significantly
    resolved_count = 0
    for hyp_id in guidelines.related_hypothesis_ids:
        hypothesis = hypotheses.get(hyp_id)
        if hypothesis:
            # Hypothesis resolved after guidelines created
            if hypothesis.last_evidence_at > guidelines.created_at:
                if hypothesis.status in ["weakening", "resolved"]:
                    resolved_count += 1

    if resolved_count >= threshold_changes:
        guidelines.mark_superseded("Related hypotheses resolved")
        return

    # Check for significant new hypotheses in same domains
    guideline_domains = set()
    for hyp_id in guidelines.related_hypothesis_ids:
        hypothesis = hypotheses.get(hyp_id)
        if hypothesis:
            guideline_domains.add(hypothesis.domain)

    new_relevant = [
        h for h in hypotheses.values()
        if h.formed_at > guidelines.created_at
        and h.status in ["forming", "active"]
        and h.domain in guideline_domains
        and h.id not in guidelines.related_hypothesis_ids
    ]

    if len(new_relevant) >= threshold_changes:
        guidelines.mark_needs_update()
