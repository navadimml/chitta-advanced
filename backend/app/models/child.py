"""
Child Model - The Core Entity

The child is the invariant center of Chitta. Everything else orbits around it.

Design principles:
- Child data is invariant (doesn't change based on who's viewing)
- Developmental understanding evolves continuously
- Exploration cycles track how understanding is built
- No workflow states - just evolving understanding

The Living Gestalt:
- We see the WHOLE child, not just difficulties
- Strengths come before concerns
- Hypotheses drive exploration
- Understanding evolves through evidence
"""

from pydantic import BaseModel, Field, field_validator, computed_field, model_serializer
from typing import List, Dict, Optional, Any
from datetime import datetime, date

from .artifact import Artifact
from .understanding import (
    DevelopmentalUnderstanding,
    Hypothesis,
    Evidence,
    Pattern,
    PendingInsight,
    SynthesisReport,
    CycleSnapshot,
)
from .exploration import (
    ExplorationCycle,
    CycleArtifact,
    VideoScenario,
    ConversationMethod,
    VideoMethod,
)


# === Identity Models ===

class ChildIdentity(BaseModel):
    """
    Core identity - the basics that rarely change.
    """
    name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None  # "male", "female", "other"

    @property
    def age_years(self) -> Optional[float]:
        """Calculate current age in years."""
        if not self.birth_date:
            return None
        today = date.today()
        age = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        # Add fractional months
        months_diff = today.month - self.birth_date.month
        if today.day < self.birth_date.day:
            months_diff -= 1
        return round(age + months_diff / 12, 1)

    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v):
        """Reject placeholder values."""
        if v is None:
            return None
        placeholders = [
            'unknown', 'not mentioned', 'null', 'none',
            'לא צוין', 'לא ידוע', 'not specified'
        ]
        if v.lower().strip() in placeholders:
            return None
        if len(v.strip()) < 2:
            return None
        return v.strip()


# === Essence & Strengths ===

class Essence(BaseModel):
    """
    Who is this child as a person - beyond demographics.
    Their temperament, energy, core nature.
    """
    temperament_observations: List[str] = Field(default_factory=list)
    energy_pattern: Optional[str] = None
    core_qualities: List[str] = Field(default_factory=list)


class Strengths(BaseModel):
    """
    What this child does well - elevated to first-class status.
    Strengths reveal capacity and provide intervention pathways.
    """
    abilities: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    what_lights_them_up: Optional[str] = None
    surprises_people: Optional[str] = None


# === Concerns ===

class ConcernDetail(BaseModel):
    """A specific concern with context."""
    area: str  # "speech", "motor", "social", etc.
    description: str
    examples: List[str] = Field(default_factory=list)
    since_when: Optional[str] = None
    impact: Optional[str] = None


class Concerns(BaseModel):
    """
    Parent's concerns - in context of the whole child.
    Concerns are NOT the child's identity.
    """
    primary_areas: List[str] = Field(default_factory=list)
    details: List[ConcernDetail] = Field(default_factory=list)
    parent_narrative: Optional[str] = None  # In their own words


# === History ===

class BirthHistory(BaseModel):
    """Birth and early history."""
    complications: Optional[str] = None
    premature: Optional[bool] = None
    weeks_gestation: Optional[int] = None
    early_medical: Optional[str] = None


class PreviousEvaluation(BaseModel):
    """Record of a professional evaluation."""
    evaluator_type: str
    date_approximate: Optional[str] = None
    findings: Optional[str] = None
    diagnosis_given: Optional[str] = None


class DevelopmentalHistory(BaseModel):
    """Complete history - what happened before we met."""
    birth: BirthHistory = Field(default_factory=BirthHistory)
    early_development: Optional[str] = None
    milestone_notes: Optional[str] = None
    medical_history: Optional[str] = None
    previous_evaluations: List[PreviousEvaluation] = Field(default_factory=list)
    previous_diagnoses: List[str] = Field(default_factory=list)


# === Family ===

class Sibling(BaseModel):
    """Information about a sibling."""
    position: str  # "older", "younger", "twin"
    age_or_gap: Optional[str] = None
    notes: Optional[str] = None  # "speaks for him", "very close"


class FamilyContext(BaseModel):
    """Family context - who surrounds this child."""
    structure: Optional[str] = None
    siblings: List[Sibling] = Field(default_factory=list)
    languages_at_home: List[str] = Field(default_factory=list)
    family_developmental_history: Optional[str] = None  # "dad was late talker"
    support_system: Optional[str] = None


# === Videos & Journal ===

class Video(BaseModel):
    """A behavioral observation video."""
    id: str
    scenario: str  # What was filmed
    uploaded_at: datetime = Field(default_factory=datetime.now)
    duration_seconds: int = 0

    # Storage
    file_path: Optional[str] = None
    file_url: Optional[str] = None

    # Analysis context (from guidelines)
    analyst_context: Optional[Dict[str, Any]] = None

    # Analysis tracking
    analysis_status: str = "pending"  # "pending", "analyzing", "ready", "error"
    analysis_artifact_id: Optional[str] = None
    analysis_error: Optional[str] = None


class JournalEntry(BaseModel):
    """A moment captured from conversation."""
    id: str
    content: str
    context: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    themes: List[str] = Field(default_factory=list)


# === The Child Model ===

class Child(BaseModel):
    """
    The Child - the invariant core entity.

    Everything in Chitta orbits around the child. This model contains:
    - Identity (name, age, gender)
    - Essence (temperament, core qualities)
    - Strengths (what they do well)
    - Concerns (what parent is worried about)
    - History (what came before)
    - Family (who surrounds them)
    - Understanding (hypotheses, patterns, evidence - the Living Gestalt)
    - Exploration cycles (how we're building understanding)
    - Artifacts (generated reports, guidelines)
    - Videos & Journal (observations)
    """
    model_config = {"populate_by_name": True}

    id: str = Field(description="Unique identifier", alias="child_id")

    # === IDENTITY ===
    identity: ChildIdentity = Field(default_factory=ChildIdentity)

    # === ESSENCE (who they are) ===
    essence: Essence = Field(default_factory=Essence)

    # === STRENGTHS (first-class, not afterthought) ===
    strengths: Strengths = Field(default_factory=Strengths)

    # === CONCERNS (in context) ===
    concerns: Concerns = Field(default_factory=Concerns)

    # === HISTORY ===
    history: DevelopmentalHistory = Field(default_factory=DevelopmentalHistory)

    # === FAMILY ===
    family: FamilyContext = Field(default_factory=FamilyContext)

    # === UNDERSTANDING (the Living Gestalt) ===
    understanding: DevelopmentalUnderstanding = Field(default_factory=DevelopmentalUnderstanding)

    # === EXPLORATION CYCLES ===
    exploration_cycles: List[ExplorationCycle] = Field(default_factory=list)

    # === SYNTHESIS REPORTS (Cross-Cycle) ===
    # Unlike cycle artifacts, synthesis reports span multiple cycles
    # and tell the longitudinal story of development
    synthesis_reports: List[SynthesisReport] = Field(default_factory=list)

    # Artifacts are now stored ONLY in exploration cycles.
    # Access them via the `artifacts` computed property below.

    # === VIDEOS ===
    videos: List[Video] = Field(default_factory=list)

    # === JOURNAL ===
    journal_entries: List[JournalEntry] = Field(default_factory=list)

    # === METADATA ===
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # === Convenience Properties ===

    @property
    def name(self) -> Optional[str]:
        return self.identity.name

    @property
    def age(self) -> Optional[float]:
        return self.identity.age_years

    @property
    def profile_summary(self) -> str:
        parts = []
        if self.name:
            parts.append(self.name)
        if self.age:
            parts.append(f"גיל {self.age}")
        return " ".join(parts) if parts else "ילד/ה"

    # === Backward Compatibility Properties ===

    @property
    def developmental_data(self) -> "DevelopmentalData":
        """
        DEPRECATED: Backward compatibility property.

        Maps new structured data to old flat DevelopmentalData format.
        Used by old services until they're migrated.
        """
        # Extract daily_routines from essence.temperament_observations
        daily_routines = None
        for obs in self.essence.temperament_observations:
            if obs.startswith("Daily routines: "):
                daily_routines = obs.replace("Daily routines: ", "")
                break

        # Extract parent_goals from understanding.pending_insights
        parent_goals = None
        for insight in self.understanding.pending_insights:
            if insight.source == "parent_goal":
                parent_goals = insight.content
                break

        # Extract urgent_flags from understanding.pending_insights
        urgent_flags = [
            insight.content
            for insight in self.understanding.pending_insights
            if insight.source == "urgent_flag"
        ]

        return DevelopmentalData(
            child_name=self.identity.name,
            age=self.identity.age_years,
            gender=self.identity.gender,
            primary_concerns=self.concerns.primary_areas,
            concern_details=self.concerns.parent_narrative,
            strengths=self.strengths.abilities + self.strengths.interests,
            family_context=self.family.structure,
            developmental_history=self.history.early_development,
            daily_routines=daily_routines,
            parent_goals=parent_goals,
            urgent_flags=urgent_flags,
        )

    @property
    def data_completeness(self) -> float:
        """DEPRECATED: Backward compatibility for completeness score."""
        # Simple heuristic based on filled fields
        score = 0.0
        if self.identity.name:
            score += 0.15
        if self.identity.age_years:
            score += 0.15
        if self.concerns.primary_areas:
            score += 0.2
        if self.strengths.abilities or self.strengths.interests:
            score += 0.15
        if self.history.early_development or self.history.milestone_notes:
            score += 0.15
        if self.family.structure or self.family.siblings:
            score += 0.1
        if self.understanding.hypotheses:
            score += 0.1
        return min(score, 1.0)

    # === Exploration Cycle Management ===

    def active_exploration_cycles(self) -> List[ExplorationCycle]:
        """Get cycles that are not complete."""
        return [c for c in self.exploration_cycles if c.status != "complete"]

    def get_cycle(self, cycle_id: str) -> Optional[ExplorationCycle]:
        return next((c for c in self.exploration_cycles if c.id == cycle_id), None)

    def current_cycle(self) -> Optional[ExplorationCycle]:
        """The most recent active cycle."""
        active = self.active_exploration_cycles()
        return active[-1] if active else None

    def add_cycle(self, cycle: ExplorationCycle):
        self.exploration_cycles.append(cycle)
        self.updated_at = datetime.now()

    # === Artifact Management ===
    # Artifacts now live in exploration cycles. These methods provide
    # backwards-compatible access by aggregating from all cycles.

    @computed_field
    @property
    def artifacts(self) -> Dict[str, Artifact]:
        """
        Aggregate all artifacts from exploration cycles.
        Returns a dict for backwards compatibility with existing code.
        This is a computed field so it gets serialized with the model.
        """
        import json
        result = {}
        for cycle in self.exploration_cycles:
            for cycle_artifact in cycle.artifacts:
                # Convert content dict to JSON string for Artifact compatibility
                content_str = json.dumps(cycle_artifact.content, ensure_ascii=False) if isinstance(cycle_artifact.content, dict) else str(cycle_artifact.content)
                # Convert CycleArtifact to Artifact for backwards compatibility
                artifact = Artifact(
                    artifact_id=cycle_artifact.id,
                    artifact_type=cycle_artifact.type,
                    status=cycle_artifact.status,
                    content=content_str,
                    content_format=cycle_artifact.content_format,
                    metadata={"cycle_id": cycle.id},
                    created_at=cycle_artifact.created_at,
                    updated_at=cycle_artifact.updated_at,
                    ready_at=cycle_artifact.ready_at,
                )
                result[cycle_artifact.id] = artifact
        return result

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID, searching across all cycles."""
        return self.artifacts.get(artifact_id)

    def has_artifact(self, artifact_id: str) -> bool:
        """Check if artifact exists in any cycle."""
        return self.get_artifact(artifact_id) is not None

    def add_artifact(self, artifact: Artifact):
        """
        Add artifact to current exploration cycle.
        Creates a new cycle if none exists.
        """
        import json
        current_cycle = self.current_cycle()
        if not current_cycle:
            # Create a general-purpose cycle
            current_cycle = ExplorationCycle(
                focus_description="General exploration",
                status="active",
            )
            self.add_cycle(current_cycle)

        # Convert content from string to dict for CycleArtifact
        content_dict = {}
        if artifact.content:
            if isinstance(artifact.content, dict):
                content_dict = artifact.content
            elif isinstance(artifact.content, str):
                try:
                    content_dict = json.loads(artifact.content)
                except json.JSONDecodeError:
                    content_dict = {"text": artifact.content}

        # Convert Artifact to CycleArtifact
        cycle_artifact = CycleArtifact(
            id=artifact.artifact_id,
            type=artifact.artifact_type,
            content=content_dict,
            content_format=artifact.content_format,
            status=artifact.status,
        )
        if artifact.ready_at:
            cycle_artifact.ready_at = artifact.ready_at
        current_cycle.add_artifact(cycle_artifact)
        self.updated_at = datetime.now()

    # === Video Management ===

    def add_video(self, video: Video):
        self.videos.append(video)
        self.updated_at = datetime.now()

    def get_video(self, video_id: str) -> Optional[Video]:
        return next((v for v in self.videos if v.id == video_id), None)

    def videos_pending_analysis(self) -> List[Video]:
        return [v for v in self.videos if v.analysis_status == "pending"]

    def analyzed_videos(self) -> List[Video]:
        return [v for v in self.videos if v.analysis_status == "ready"]

    @property
    def video_count(self) -> int:
        return len(self.videos)

    # === Journal Management ===

    def add_journal_entry(self, entry: JournalEntry):
        self.journal_entries.append(entry)
        self.updated_at = datetime.now()

    def recent_journal_entries(self, limit: int = 10) -> List[JournalEntry]:
        sorted_entries = sorted(
            self.journal_entries,
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_entries[:limit]

    # === Hypothesis Management (Cycle-Owned) ===
    # With the temporal design, hypotheses are OWNED by exploration cycles.
    # These methods aggregate from cycles for convenience, with backward
    # compatibility for legacy understanding.hypotheses.

    def active_hypotheses(self) -> List[Hypothesis]:
        """
        Get all active hypotheses across all active cycles.

        TEMPORAL DESIGN: Hypotheses are owned by cycles. This aggregates
        from all active exploration cycles. Also checks legacy
        understanding.hypotheses for backward compatibility.
        """
        result = []
        # Primary: get from active exploration cycles
        for cycle in self.active_exploration_cycles():
            result.extend(cycle.active_hypotheses())
        # Backward compat: also check legacy understanding.hypotheses
        result.extend(self.understanding.active_hypotheses())
        return result

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """
        Find a hypothesis by ID across all cycles.

        Searches exploration cycles first (new model), then falls back
        to understanding.hypotheses (legacy).
        """
        # Search in exploration cycles first
        for cycle in self.exploration_cycles:
            hypothesis = cycle.get_hypothesis(hypothesis_id)
            if hypothesis:
                return hypothesis
        # Fall back to legacy understanding
        return self.understanding.get_hypothesis(hypothesis_id)

    def add_hypothesis(self, hypothesis: Hypothesis, cycle: Optional[ExplorationCycle] = None):
        """
        Add a hypothesis to a cycle.

        TEMPORAL DESIGN (One Domain = One Cycle):
        - Each domain gets its own cycle
        - Never mix domains in one cycle
        - If cycle is specified, use it (caller is responsible for domain)
        - If no cycle specified, find/create cycle for this hypothesis's domain
        """
        if cycle is None:
            # === TEMPORAL DESIGN: One Domain = One Cycle ===
            # Find an active cycle for THIS domain
            matching_cycle = None
            for c in self.active_exploration_cycles():
                if c.focus_domain == hypothesis.domain:
                    matching_cycle = c
                    break

            if matching_cycle:
                cycle = matching_cycle
            else:
                # Create a NEW cycle for this domain
                cycle = ExplorationCycle(
                    focus_description=f"Exploring: {hypothesis.theory[:80]}",
                    focus_domain=hypothesis.domain,
                    status="active",
                )
                self.add_cycle(cycle)

        # Add to cycle (primary ownership)
        cycle.add_hypothesis(hypothesis)
        # Also add to understanding for backward compatibility
        self.understanding.add_hypothesis(hypothesis)
        self.updated_at = datetime.now()

    def add_pattern(self, pattern: Pattern):
        """
        Add a cross-cycle pattern.

        TEMPORAL DESIGN: Patterns are observations ACROSS cycles, so they
        live in understanding (not owned by a single cycle).
        """
        self.understanding.add_pattern(pattern)
        self.updated_at = datetime.now()

    def add_evidence_to_hypothesis(
        self,
        hypothesis_id: str,
        evidence: Evidence,
        effect: str = "neutral"
    ):
        """
        Add evidence to a hypothesis.

        Searches for the hypothesis across all cycles and legacy understanding.
        """
        # First try to find in cycles
        for cycle in self.exploration_cycles:
            hypothesis = cycle.get_hypothesis(hypothesis_id)
            if hypothesis:
                hypothesis.add_evidence(evidence, effect)
                cycle.updated_at = datetime.now()
                self.updated_at = datetime.now()
                return

        # Fall back to legacy understanding
        hypothesis = self.understanding.get_hypothesis(hypothesis_id)
        if hypothesis:
            hypothesis.add_evidence(evidence, effect)
            self.updated_at = datetime.now()

    def hypotheses_for_domain(self, domain: str) -> List[Hypothesis]:
        """
        Get all hypotheses for a domain across all cycles.

        Useful for cross-cycle analysis of a specific developmental area.
        """
        result = []
        for cycle in self.exploration_cycles:
            result.extend(cycle.hypotheses_for_domain(domain))
        # Also check legacy
        result.extend(self.understanding.hypotheses_for_domain(domain))
        return result

    def all_hypotheses(self) -> List[Hypothesis]:
        """
        Get ALL hypotheses across all cycles and statuses.

        Includes completed cycles (historical record) and legacy hypotheses.
        """
        result = []
        for cycle in self.exploration_cycles:
            result.extend(cycle.hypotheses)
        result.extend(self.understanding.hypotheses)
        return result


# === Backward Compatibility Layer ===
# These aliases allow old code to continue working during migration.
# They should be removed once all services are updated.

class DevelopmentalData(BaseModel):
    """
    DEPRECATED: Backward compatibility wrapper.

    Maps old flat developmental data structure to new Living Gestalt model.
    Old code expecting developmental_data can use this until migrated.
    """
    # Identity
    child_name: Optional[str] = None
    age: Optional[float] = None
    gender: Optional[str] = None

    # Old flat structure (these map to new structured models)
    primary_concerns: List[str] = Field(default_factory=list)
    concern_details: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    family_context: Optional[str] = None
    developmental_history: Optional[str] = None
    daily_routines: Optional[str] = None
    parent_goals: Optional[str] = None

    # Legacy fields
    filming_preference: Optional[str] = None
    interaction_style: Optional[str] = None
    parent_emotional_state: Optional[str] = None
    specific_examples: List[str] = Field(default_factory=list)
    urgent_flags: List[str] = Field(default_factory=list)

    # Metadata (for backward compat with child_service)
    last_updated: datetime = Field(default_factory=datetime.now)
    extraction_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(exclude_none=True)


class DomainObservation(BaseModel):
    """DEPRECATED: For backward compatibility."""
    observation: str
    source: str = "conversation"
    timestamp: datetime = Field(default_factory=datetime.now)


class DevelopmentalDomains(BaseModel):
    """DEPRECATED: Backward compatibility wrapper."""
    language_receptive: List[DomainObservation] = Field(default_factory=list)
    language_expressive: List[DomainObservation] = Field(default_factory=list)
    language_pragmatic: List[DomainObservation] = Field(default_factory=list)
    social_relationships: List[DomainObservation] = Field(default_factory=list)
    emotional_regulation: List[DomainObservation] = Field(default_factory=list)
    social_awareness: List[DomainObservation] = Field(default_factory=list)
    cognitive: List[DomainObservation] = Field(default_factory=list)
    motor_gross: List[DomainObservation] = Field(default_factory=list)
    motor_fine: List[DomainObservation] = Field(default_factory=list)
    sensory_processing: List[DomainObservation] = Field(default_factory=list)
    play_and_imagination: List[DomainObservation] = Field(default_factory=list)
    adaptive_skills: List[DomainObservation] = Field(default_factory=list)


class Intervention(BaseModel):
    """DEPRECATED: For backward compatibility."""
    intervention_type: str
    status: str = "unknown"
    duration: Optional[str] = None
    outcome: Optional[str] = None


class EvidenceItem(BaseModel):
    """DEPRECATED: Use Evidence from understanding.py instead."""
    content: str
    source_type: str
    source_id: Optional[str] = None
    collected_at: datetime = Field(default_factory=datetime.now)
    collected_in_cycle: Optional[str] = None


class OpenQuestion(BaseModel):
    """DEPRECATED: For backward compatibility."""
    id: str
    question: str
    arose_from: Optional[str] = None
    arose_from_cycle: Optional[str] = None
    priority: str = "medium"
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "open"
    explored_in_cycles: List[str] = Field(default_factory=list)
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None


class LivingEdge(BaseModel):
    """DEPRECATED: Use DevelopmentalUnderstanding from understanding.py."""
    patterns: List[Pattern] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    open_questions: List[OpenQuestion] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                return h
        return None

    @property
    def active_hypotheses(self) -> List[Hypothesis]:
        return [h for h in self.hypotheses if h.status in ["forming", "active"]]


# More backward compatibility classes needed by gestalt.py

class ChildHistory(BaseModel):
    """DEPRECATED: Use DevelopmentalHistory."""
    birth: BirthHistory = Field(default_factory=BirthHistory)
    early_development: Optional[str] = None
    milestone_notes: Optional[str] = None
    medical_history: Optional[str] = None
    previous_evaluations: List[PreviousEvaluation] = Field(default_factory=list)
    previous_diagnoses: List[str] = Field(default_factory=list)
    interventions: List[Intervention] = Field(default_factory=list)


class Family(BaseModel):
    """DEPRECATED: Use FamilyContext."""
    structure: Optional[str] = None
    siblings: List[Sibling] = Field(default_factory=list)
    who_at_home: Optional[str] = None
    languages_at_home: List[str] = Field(default_factory=list)
    family_developmental_history: Optional[str] = None
    support_system: Optional[str] = None
    cultural_context: Optional[str] = None


class CurrentFocus(BaseModel):
    """DEPRECATED: Focus tracking."""
    hypothesis_ids: List[str] = Field(default_factory=list)
    question_ids: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    why: Optional[str] = None


class SynthesisSnapshot(BaseModel):
    """DEPRECATED: Synthesis snapshot."""
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    artifact_id: str
    trigger: str
    gestalt_summary_at_time: Optional[str] = None
    completeness_at_time: float = 0.0
    active_hypotheses_at_time: List[str] = Field(default_factory=list)
    patterns_included: List[str] = Field(default_factory=list)
    superseded_by: Optional[str] = None
    significant_changes_since: List[str] = Field(default_factory=list)
    is_current: bool = True


class ExplorationActivity(BaseModel):
    """DEPRECATED: Exploration activity tracking."""
    cycles: List[ExplorationCycle] = Field(default_factory=list)
    syntheses: List[SynthesisSnapshot] = Field(default_factory=list)
    current_focus: Optional[CurrentFocus] = None

    @property
    def active_cycles(self) -> List[ExplorationCycle]:
        return [c for c in self.cycles if c.status != "complete"]

    @property
    def current_synthesis(self) -> Optional[SynthesisSnapshot]:
        current = [s for s in self.syntheses if s.is_current]
        return current[-1] if current else None


# Re-export exploration classes for backward compatibility
from .exploration import (
    VideoScenario,
    ConversationMethod,
    ConversationQuestion,
    VideoMethod,
)
