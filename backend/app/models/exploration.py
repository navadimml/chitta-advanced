"""
Exploration Cycle Models

Artifacts belong to exploration cycles, not floating freely.
Each cycle explores specific hypotheses through various methods
(conversation, video, etc.) and produces artifacts along the way.

Cycle lifecycle:
- active: Building understanding through conversation
- evidence_gathering: Have guidelines, waiting for videos
- synthesizing: Videos uploaded, analyzing and creating report
- complete: Done (but journey continues with new cycles)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


class CycleArtifact(BaseModel):
    """
    Artifact produced within an exploration cycle.

    Artifacts are tied to cycles and hypotheses.
    They have lifecycle states that drive card visibility.
    """
    id: str = Field(default_factory=generate_id)
    type: str  # "video_guidelines", "video_analysis", "synthesis_report"
    content: Dict[str, Any] = Field(default_factory=dict)

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

    # Staleness tracking
    superseded_by: Optional[str] = None  # New artifact ID if replaced
    superseded_reason: Optional[str] = None

    def mark_ready(self):
        self.status = "ready"
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
    A cycle of exploration around specific hypotheses.

    A cycle has a clear focus (hypotheses), uses various methods
    (conversation, video), and produces artifacts along the way.

    Multiple cycles can be active - exploring different aspects
    of the child's development.
    """
    id: str = Field(default_factory=generate_id)

    # What we're exploring
    hypothesis_ids: List[str] = Field(default_factory=list)
    focus_description: Optional[str] = None  # "Exploring motor concerns and transitions"

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
