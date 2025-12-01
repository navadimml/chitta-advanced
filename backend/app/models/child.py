"""
Child Model - The Core Entity

The child is the invariant center of Chitta. Everything else orbits around it.
Child data accumulates over time and is shared across all users with access.

Design principles:
- Child data is invariant (doesn't change based on who's viewing)
- Artifacts, videos, journal entries belong to the child
- Developmental understanding evolves continuously
- No workflow states - just evolving understanding

The Living Gestalt:
- We see the WHOLE child, not just difficulties
- Strengths come before concerns
- Patterns and hypotheses drive exploration
- Understanding evolves through conversation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum

from .artifact import Artifact


# === Living Gestalt Component Models ===

class Essence(BaseModel):
    """
    Who is this child as a person - beyond demographics.

    This captures the child's core nature: temperament, energy,
    and the qualities that make them who they are.
    """
    temperament_observations: List[str] = Field(default_factory=list)
    # e.g., ["slow to warm", "cautious with new people", "intense when engaged"]

    energy_pattern: Optional[str] = None
    # e.g., "high energy but can focus deeply on interests"

    core_qualities: List[str] = Field(default_factory=list)
    # e.g., ["curious", "loving", "determined", "sensitive"]


class Strengths(BaseModel):
    """
    What this child does well - elevated to first-class status.

    Strengths are not afterthoughts. They:
    - Reveal capacity
    - Provide intervention pathways
    - Contextualize difficulties
    - Build trust with parents
    """
    abilities: List[str] = Field(default_factory=list)
    # e.g., ["great memory", "problem solver", "creative"]

    interests: List[str] = Field(default_factory=list)
    # e.g., ["dinosaurs", "music", "cars", "water play"]

    what_lights_them_up: Optional[str] = None
    # Narrative: "His whole face changes when music plays..."

    surprises_people: Optional[str] = None
    # "People don't expect how much he understands..."


class DomainObservation(BaseModel):
    """A single observation about a developmental domain."""
    observation: str
    source: str = "conversation"  # "conversation" | "video" | "story"
    timestamp: datetime = Field(default_factory=datetime.now)


class DevelopmentalDomains(BaseModel):
    """
    Structured view of all developmental domains.

    Not just concerns - the FULL picture of where the child
    is across all areas of development.
    """
    # Language & Communication
    language_receptive: List[DomainObservation] = Field(default_factory=list)
    language_expressive: List[DomainObservation] = Field(default_factory=list)
    language_pragmatic: List[DomainObservation] = Field(default_factory=list)

    # Social-Emotional
    social_relationships: List[DomainObservation] = Field(default_factory=list)
    emotional_regulation: List[DomainObservation] = Field(default_factory=list)
    social_awareness: List[DomainObservation] = Field(default_factory=list)

    # Cognitive
    cognitive: List[DomainObservation] = Field(default_factory=list)

    # Motor
    motor_gross: List[DomainObservation] = Field(default_factory=list)
    motor_fine: List[DomainObservation] = Field(default_factory=list)

    # Sensory
    sensory_processing: List[DomainObservation] = Field(default_factory=list)

    # Play
    play_and_imagination: List[DomainObservation] = Field(default_factory=list)

    # Adaptive/Daily Living
    adaptive_skills: List[DomainObservation] = Field(default_factory=list)


class BirthHistory(BaseModel):
    """Birth and early history - critical for interpretation."""
    complications: Optional[str] = None
    premature: Optional[bool] = None
    weeks_gestation: Optional[int] = None  # if premature
    nicu_stay: Optional[bool] = None
    early_medical_issues: Optional[str] = None


class PreviousEvaluation(BaseModel):
    """Record of a previous professional evaluation."""
    evaluator_type: str  # "neurologist", "speech therapist", etc.
    date_approximate: Optional[str] = None
    findings: Optional[str] = None
    diagnosis_given: Optional[str] = None


class Intervention(BaseModel):
    """Record of a therapy or intervention."""
    intervention_type: str  # "speech therapy", "OT", etc.
    status: str = "unknown"  # "current", "past", "unknown"
    duration: Optional[str] = None
    outcome: Optional[str] = None  # "helpful", "not helpful", etc.


class Sibling(BaseModel):
    """Information about a sibling."""
    position: str  # "older", "younger", "twin"
    age_or_gap: Optional[str] = None
    notes: Optional[str] = None  # "speaks for him", "very close", etc.


class ChildHistory(BaseModel):
    """
    Complete history - what happened before we met.

    History informs interpretation. A 32-week preemie at age 3
    is developmentally different from a full-term 3-year-old.
    """
    birth: BirthHistory = Field(default_factory=BirthHistory)
    early_development: Optional[str] = None  # general narrative
    milestone_notes: Optional[str] = None  # "walked at 14 months, first words at 18 months"
    medical_history: Optional[str] = None
    previous_evaluations: List[PreviousEvaluation] = Field(default_factory=list)
    previous_diagnoses: List[str] = Field(default_factory=list)
    interventions: List[Intervention] = Field(default_factory=list)


class Family(BaseModel):
    """
    Family context - who surrounds this child.

    Family dynamics affect development. "Sister speaks for him"
    changes how we interpret speech delay.
    """
    structure: Optional[str] = None  # "two parents, older sister"
    siblings: List[Sibling] = Field(default_factory=list)
    who_at_home: Optional[str] = None
    languages_at_home: List[str] = Field(default_factory=list)
    family_developmental_history: Optional[str] = None  # "dad was late talker"
    support_system: Optional[str] = None
    cultural_context: Optional[str] = None


class Pattern(BaseModel):
    """
    A detected pattern - theme appearing across observations.

    Patterns emerge when we notice the same theme in different contexts:
    - "Mornings are hard" + "car seat battles" + "bedtime struggles"
      = Pattern: "Transitions are difficult"

    Patterns can trigger hypotheses and be explored further.
    """
    id: str  # Unique identifier for linking
    theme: str  # "transitions are difficult"
    observations: List[str] = Field(default_factory=list)  # the evidence
    domains_involved: List[str] = Field(default_factory=list)  # which areas
    detected_at: datetime = Field(default_factory=datetime.now)
    confidence: float = 0.5  # 0-1

    # Linking
    spawned_hypothesis_ids: List[str] = Field(default_factory=list)  # Hypotheses formed from this pattern
    detected_in_cycle: Optional[str] = None  # Which exploration cycle found this


class EvidenceItem(BaseModel):
    """
    A piece of evidence for or against a hypothesis.

    Evidence can come from conversation, video, or external sources.
    Tracking evidence allows us to see HOW understanding evolved.
    """
    content: str  # What was observed/said
    source_type: str  # "conversation", "video_analysis", "parent_report", "story"
    source_id: Optional[str] = None  # Reference to source (story_id, video_id, etc.)
    collected_at: datetime = Field(default_factory=datetime.now)
    collected_in_cycle: Optional[str] = None  # Which exploration cycle found this


class Hypothesis(BaseModel):
    """
    A working theory - held lightly, open to revision.

    Not "Daniel has autism" but "Daniel's speech delay might be
    primarily temperament-related - capacity is there, safety is the key."

    Hypotheses come from THREE SOURCES:
    1. DOMAIN KNOWLEDGE - Clinical patterns (comorbidity)
       e.g., "Speech delay → motor planning might be involved"
    2. PATTERNS - Themes connecting observations
       e.g., "Mornings hard + car seat + bedtime → Transitions are difficult"
    3. CONTRADICTIONS - Things that don't fit
       e.g., "Usually withdrawn but spontaneous with grandma"

    Hypotheses are LINKED to exploration cycles that test them,
    creating a traceable history of how understanding evolved.
    """
    id: str  # Unique identifier for linking
    theory: str

    # === SOURCE: Where did this hypothesis come from? ===
    source: str = "pattern"  # "pattern", "domain_knowledge", "contradiction"
    source_details: Optional[str] = None  # Specific trigger description

    # For pattern-based hypotheses
    arose_from_pattern_id: Optional[str] = None

    # For domain-knowledge hypotheses (comorbidity)
    triggered_by_concern: Optional[str] = None  # e.g., "speech_delay"
    clinical_connection: Optional[str] = None  # e.g., "motor planning often co-occurs"

    # For contradiction-based hypotheses
    contradiction: Optional[str] = None  # e.g., "Usually X but with grandma Y"

    # Related developmental domains
    related_domains: List[str] = Field(default_factory=list)

    # Questions that would test this hypothesis
    questions_to_explore: List[str] = Field(default_factory=list)

    # === EVIDENCE ===
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list)
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list)

    # === STATUS ===
    status: str = "exploring"  # "exploring", "strengthening", "weakening", "supported", "contradicted", "revised", "archived"
    formed_at: datetime = Field(default_factory=datetime.now)

    # === EXPLORATION TRACKING ===
    exploration_cycles: List[str] = Field(default_factory=list)  # IDs of cycles that explored this

    # === EVOLUTION ===
    revised_to: Optional[str] = None  # ID of hypothesis this evolved into
    revision_reason: Optional[str] = None

    @property
    def evidence_count(self) -> int:
        return len(self.supporting_evidence) + len(self.contradicting_evidence)

    @property
    def support_ratio(self) -> float:
        """Ratio of supporting to total evidence (0-1)."""
        total = self.evidence_count
        if total == 0:
            return 0.5  # No evidence = neutral
        return len(self.supporting_evidence) / total

    @property
    def is_from_domain_knowledge(self) -> bool:
        return self.source == "domain_knowledge"

    @property
    def is_from_pattern(self) -> bool:
        return self.source == "pattern"

    @property
    def is_from_contradiction(self) -> bool:
        return self.source == "contradiction"


class OpenQuestion(BaseModel):
    """
    Something we're still wondering about.

    Open questions keep the Gestalt alive. They drive curiosity
    and guide future exploration. Questions can drive exploration cycles.
    """
    id: str  # Unique identifier for linking
    question: str  # "What's different about grandmother?"
    arose_from: Optional[str] = None  # context
    arose_from_cycle: Optional[str] = None  # Which exploration cycle raised this
    priority: str = "medium"  # "high", "medium", "low"
    created_at: datetime = Field(default_factory=datetime.now)

    # Resolution
    status: str = "open"  # "open", "exploring", "answered", "archived"
    explored_in_cycles: List[str] = Field(default_factory=list)  # Cycles that explored this
    answer: Optional[str] = None  # What we learned
    answered_at: Optional[datetime] = None


class LivingEdge(BaseModel):
    """
    The living edge of understanding - what keeps the Gestalt alive.

    This holds the dynamic elements: patterns we've noticed,
    theories we're exploring, questions we're wondering about.

    All elements can link to exploration cycles, creating a traceable
    history of how understanding evolved.
    """
    patterns: List[Pattern] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    open_questions: List[OpenQuestion] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    # Things that don't fit yet: "Usually cautious but spontaneous with grandma"

    # === Convenience Methods ===

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get a hypothesis by ID."""
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                return h
        return None

    def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Get a pattern by ID."""
        for p in self.patterns:
            if p.id == pattern_id:
                return p
        return None

    def get_question(self, question_id: str) -> Optional[OpenQuestion]:
        """Get a question by ID."""
        for q in self.open_questions:
            if q.id == question_id:
                return q
        return None

    @property
    def active_hypotheses(self) -> List[Hypothesis]:
        """Hypotheses currently being explored (not archived/resolved)."""
        return [h for h in self.hypotheses if h.status in ["exploring", "strengthening", "weakening"]]

    @property
    def open_questions_list(self) -> List[OpenQuestion]:
        """Questions that are still open."""
        return [q for q in self.open_questions if q.status == "open"]

    @property
    def high_priority_questions(self) -> List[OpenQuestion]:
        """High priority open questions."""
        return [q for q in self.open_questions if q.status == "open" and q.priority == "high"]


# === Activity-Based Tracking Models ===
# These replace the old state-based tracking (has_video_guidelines, has_parent_report)
# with purpose-driven, ongoing activity tracking.


# --- Method-Specific Details (nested in ExplorationCycle) ---

class ConversationQuestion(BaseModel):
    """
    A question asked during conversation exploration.

    Tracks what we asked and what we learned from the answer.
    """
    question: str  # What we asked
    target_hypothesis_id: Optional[str] = None  # Hypothesis ID this tests
    what_we_hoped_to_learn: str  # Why we asked this
    asked_at: datetime = Field(default_factory=datetime.now)

    # Response tracking
    response_summary: Optional[str] = None  # What the parent said
    evidence_produced: Optional[str] = None  # What this revealed
    evidence_direction: Optional[str] = None  # "supports", "contradicts", "neutral", "unclear"
    answered_at: Optional[datetime] = None


class ConversationMethod(BaseModel):
    """
    Conversation-specific exploration details.

    Tracks questions asked and stories elicited through dialogue.
    """
    questions: List[ConversationQuestion] = Field(default_factory=list)
    stories_elicited: List[str] = Field(default_factory=list)  # Story/journal entry IDs

    @property
    def has_pending_questions(self) -> bool:
        return any(q.response_summary is None for q in self.questions)

    @property
    def pending_questions(self) -> List[ConversationQuestion]:
        return [q for q in self.questions if q.response_summary is None]


class VideoScenario(BaseModel):
    """A specific video scenario requested."""
    scenario: str  # "playing alone with blocks"
    why_we_want_to_see: str  # "to observe focus and frustration tolerance"
    target_hypothesis_id: Optional[str] = None  # What hypothesis this tests
    focus_points: List[str] = Field(default_factory=list)
    duration_guidance: str = "medium"  # "short", "medium", "long"

    # Status
    requested_at: datetime = Field(default_factory=datetime.now)
    video_id: Optional[str] = None  # filled when video received
    received_at: Optional[datetime] = None
    analysis_id: Optional[str] = None  # filled when analyzed


class VideoMethod(BaseModel):
    """
    Video-specific exploration details.

    Tracks scenarios requested, videos received, and analyses completed.
    """
    # Why we need video (not just conversation)
    what_conversation_cant_answer: Optional[str] = None

    # Requests
    scenarios: List[VideoScenario] = Field(default_factory=list)
    guidelines_artifact_id: Optional[str] = None  # The filming guide artifact

    # Outcomes
    videos_received: List[str] = Field(default_factory=list)  # video IDs
    analysis_artifact_ids: List[str] = Field(default_factory=list)

    @property
    def is_waiting_for_videos(self) -> bool:
        return any(s.video_id is None for s in self.scenarios)

    @property
    def pending_scenarios(self) -> List[VideoScenario]:
        return [s for s in self.scenarios if s.video_id is None]

    @property
    def has_unanalyzed_videos(self) -> bool:
        return any(s.video_id and not s.analysis_id for s in self.scenarios)


# --- The Unified Exploration Cycle ---

class ExplorationCycle(BaseModel):
    """
    A unified exploration cycle - testing hypotheses through any method.

    This is the CORE exploration pattern:
    1. PURPOSE: What hypotheses/questions are we exploring?
    2. METHODS: How are we exploring? (conversation, video, or both)
    3. EVIDENCE: What have we collected?
    4. LEARNINGS: What did we discover?

    A single cycle can use multiple methods:
    - Start with conversation, escalate to video if needed
    - Use video from the start
    - Mix both throughout

    The method is an implementation detail - the cycle tracks
    the exploration regardless of how it happens.
    """
    id: str
    started_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"  # "active", "waiting", "complete", "paused", "archived"

    # === PURPOSE: What are we exploring? ===
    hypothesis_ids: List[str] = Field(default_factory=list)  # Hypotheses being tested
    open_question_ids: List[str] = Field(default_factory=list)  # Questions driving this
    exploration_goal: Optional[str] = None  # What we hope to understand

    # === METHODS: How are we exploring? ===
    methods_used: List[str] = Field(default_factory=list)  # ["conversation", "video"]

    # Method-specific details (populated based on methods_used)
    conversation: Optional[ConversationMethod] = None
    video: Optional[VideoMethod] = None
    # Future methods can be added here without changing the cycle structure

    # === EVIDENCE: What have we collected? ===
    evidence: List[EvidenceItem] = Field(default_factory=list)

    # === LEARNINGS: What did we discover? ===
    hypotheses_supported: List[str] = Field(default_factory=list)  # Hypothesis IDs
    hypotheses_contradicted: List[str] = Field(default_factory=list)
    hypotheses_revised: List[str] = Field(default_factory=list)  # Hypothesis IDs that were revised
    new_hypotheses_formed: List[str] = Field(default_factory=list)  # New hypothesis IDs
    new_patterns_noticed: List[str] = Field(default_factory=list)  # Pattern IDs
    new_questions_raised: List[str] = Field(default_factory=list)  # Question IDs
    key_insights: List[str] = Field(default_factory=list)

    # === COMPLETION ===
    completed_at: Optional[datetime] = None
    completion_summary: Optional[str] = None  # What we ultimately learned
    spawned_cycle_id: Optional[str] = None  # If this led to a follow-up cycle

    # === Convenience Properties ===

    @property
    def is_active(self) -> bool:
        return self.status in ["active", "waiting"]

    @property
    def is_waiting(self) -> bool:
        """Are we waiting for something (video, response, etc.)?"""
        if self.conversation and self.conversation.has_pending_questions:
            return True
        if self.video and self.video.is_waiting_for_videos:
            return True
        return False

    @property
    def uses_video(self) -> bool:
        return "video" in self.methods_used or self.video is not None

    @property
    def uses_conversation(self) -> bool:
        return "conversation" in self.methods_used or self.conversation is not None

    def add_conversation_method(self) -> ConversationMethod:
        """Enable conversation method for this cycle."""
        if self.conversation is None:
            self.conversation = ConversationMethod()
        if "conversation" not in self.methods_used:
            self.methods_used.append("conversation")
        return self.conversation

    def add_video_method(self, why_needed: Optional[str] = None) -> VideoMethod:
        """Enable video method for this cycle (escalate from conversation)."""
        if self.video is None:
            self.video = VideoMethod(what_conversation_cant_answer=why_needed)
        if "video" not in self.methods_used:
            self.methods_used.append("video")
        return self.video


class SynthesisSnapshot(BaseModel):
    """
    A point-in-time synthesis of understanding (e.g., a parent report).

    Reports are not one-time achievements. They're snapshots that:
    - Capture understanding at a moment
    - May become outdated as understanding evolves
    - Can be generated multiple times as needed

    This replaces the old "has_parent_report" boolean with
    temporal awareness.
    """
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    artifact_id: str  # reference to the actual artifact

    # === What triggered this synthesis? ===
    trigger: str  # "parent_requested", "exploration_complete", "milestone_reached", "scheduled"

    # === What did it capture? ===
    gestalt_summary_at_time: Optional[str] = None  # brief summary of understanding
    completeness_at_time: float = 0.0

    # Hypotheses active at time of synthesis
    active_hypotheses_at_time: List[str] = Field(default_factory=list)

    # Key patterns included
    patterns_included: List[str] = Field(default_factory=list)

    # === What has changed since? ===
    # (These are updated as the gestalt evolves)
    superseded_by: Optional[str] = None  # ID of newer synthesis if this is outdated
    significant_changes_since: List[str] = Field(default_factory=list)
    is_current: bool = True  # becomes False when significantly outdated


class ExplorationActivity(BaseModel):
    """
    Tracks all exploration activity over time.

    This is the container for exploration cycles and synthesis snapshots,
    providing a complete history of how understanding has been built.

    Exploration cycles are unified - they can use conversation, video,
    or both methods. The history shows how hypotheses were explored
    regardless of method.
    """
    # === Exploration Cycles (unified - can be conversation, video, or mixed) ===
    cycles: List[ExplorationCycle] = Field(default_factory=list)

    # === Syntheses (Reports) ===
    syntheses: List[SynthesisSnapshot] = Field(default_factory=list)

    # === Convenience Methods ===

    @property
    def current_cycle(self) -> Optional[ExplorationCycle]:
        """The currently active exploration cycle, if any."""
        active = [c for c in self.cycles if c.is_active]
        return active[-1] if active else None

    @property
    def has_active_exploration(self) -> bool:
        return self.current_cycle is not None

    @property
    def is_waiting(self) -> bool:
        """Are we waiting for videos or responses?"""
        cycle = self.current_cycle
        return cycle is not None and cycle.is_waiting

    @property
    def waiting_for_videos(self) -> bool:
        """Specifically waiting for video uploads?"""
        cycle = self.current_cycle
        return (cycle is not None and
                cycle.video is not None and
                cycle.video.is_waiting_for_videos)

    @property
    def pending_video_scenarios(self) -> List[VideoScenario]:
        """All unfulfilled video requests across active cycles."""
        pending = []
        for cycle in self.cycles:
            if cycle.is_active and cycle.video:
                pending.extend(cycle.video.pending_scenarios)
        return pending

    @property
    def pending_questions(self) -> List[ConversationQuestion]:
        """All unanswered questions across active cycles."""
        pending = []
        for cycle in self.cycles:
            if cycle.is_active and cycle.conversation:
                pending.extend(cycle.conversation.pending_questions)
        return pending

    @property
    def most_recent_synthesis(self) -> Optional[SynthesisSnapshot]:
        """Most recent synthesis snapshot."""
        if not self.syntheses:
            return None
        return max(self.syntheses, key=lambda s: s.created_at)

    @property
    def current_synthesis(self) -> Optional[SynthesisSnapshot]:
        """Most recent synthesis that's still current (not outdated)."""
        current = [s for s in self.syntheses if s.is_current]
        if not current:
            return None
        return max(current, key=lambda s: s.created_at)

    def days_since_last_synthesis(self) -> Optional[int]:
        """Days since last synthesis, for freshness tracking."""
        recent = self.most_recent_synthesis
        if not recent:
            return None
        delta = datetime.now() - recent.created_at
        return delta.days

    def get_completed_cycles(self, limit: int = 10) -> List[ExplorationCycle]:
        """Get completed exploration cycles for history."""
        completed = [c for c in self.cycles if not c.is_active]
        completed.sort(key=lambda c: c.started_at, reverse=True)
        return completed[:limit]

    def get_cycles_for_hypothesis(self, hypothesis_id: str) -> List[ExplorationCycle]:
        """Get all cycles that explored a specific hypothesis."""
        return [c for c in self.cycles if hypothesis_id in c.hypothesis_ids]


class CurrentFocus(BaseModel):
    """
    What we're actively working on NOW.

    This is the "hot state" - not the accumulated history, but what's
    relevant to the current conversation and near-term activity.
    """
    # === Active Hypotheses ===
    # These are the hypotheses we're currently exploring (not archived)
    active_hypothesis_ids: List[str] = Field(default_factory=list)

    # === What We're Waiting For ===
    pending_video_scenario_count: int = 0
    pending_analysis_video_ids: List[str] = Field(default_factory=list)

    # === What's New and Unprocessed ===
    # These drive conversation - "We got a new video!" or "Analysis is ready!"
    new_videos_not_discussed: List[str] = Field(default_factory=list)  # video IDs
    new_analyses_not_discussed: List[str] = Field(default_factory=list)  # artifact IDs
    new_syntheses_not_discussed: List[str] = Field(default_factory=list)  # synthesis IDs

    # === Burning Questions ===
    # High-priority questions driving current exploration
    priority_questions: List[str] = Field(default_factory=list)

    # === Conversation Threads ===
    # Topics we were discussing that might need continuation
    open_threads: List[Dict[str, Any]] = Field(default_factory=list)
    # Each: {topic, last_discussed, status, notes}

    # === Last Interaction ===
    last_interaction_at: Optional[datetime] = None
    last_session_emotional_tone: Optional[str] = None  # how parent seemed


class Video(BaseModel):
    """
    A behavioral observation video with analysis context.

    Videos are requested by Chitta to observe specific behaviors,
    and include the context needed for meaningful analysis.
    """
    id: str
    scenario: str  # What Chitta asked to observe (e.g., "משחק קופסה במטבח")
    uploaded_at: datetime
    duration_seconds: int = 0

    # File storage
    file_path: Optional[str] = None
    file_url: Optional[str] = None

    # Context from request (what Chitta wanted to see)
    observation_context: Optional[Dict[str, Any]] = None
    # Contains: {clinical_goal, instruction_given_to_parent, focus_points}

    # Analysis tracking
    analysis_status: str = "pending"  # "pending" | "analyzing" | "ready" | "error"
    analysis_artifact_id: Optional[str] = None
    analysis_error: Optional[str] = None


class JournalEntry(BaseModel):
    """
    A moment captured by the parent in conversation.

    Note: In Chitta, the conversation IS the journal. These entries
    are extracted from conversation when the parent shares stories
    or observations worth preserving.
    """
    id: str
    content: str  # The story/observation
    context: Optional[str] = None  # What prompted this (question asked, etc.)
    extracted_from_turn: Optional[int] = None  # Which conversation turn
    timestamp: datetime = Field(default_factory=datetime.now)

    # Optional categorization (extracted by LLM)
    themes: List[str] = Field(default_factory=list)  # ["speech", "social", etc.]
    sentiment: Optional[str] = None  # "positive", "concern", "neutral"


class DevelopmentalData(BaseModel):
    """
    The Living Gestalt - structured understanding of the whole child.

    This is extracted and accumulated from all conversations.
    It grows richer over time as we learn more.

    Structure follows the Living Gestalt philosophy:
    1. Identity (who they are)
    2. Essence (their nature)
    3. Strengths (what they do well) - ELEVATED, not afterthought
    4. Developmental picture (all domains)
    5. History (what came before)
    6. Family (who surrounds them)
    7. Concerns (in context of all above)
    8. Living edge (patterns, hypotheses, questions)

    Validation ensures we don't store placeholder values.
    """
    # === 1. IDENTITY (basics) ===
    child_name: Optional[str] = None
    age: Optional[float] = None
    gender: Optional[str] = None  # "male", "female", "unknown"
    birth_date: Optional[date] = None  # For accurate age calculation

    # === 2. ESSENCE (who they are as a person) ===
    essence: Essence = Field(default_factory=Essence)

    # === 3. STRENGTHS (elevated to first-class) ===
    strengths: Strengths = Field(default_factory=Strengths)

    # Legacy field for backward compatibility
    strengths_narrative: Optional[str] = None  # old 'strengths' string field

    # === 4. DEVELOPMENTAL PICTURE (all domains) ===
    developmental_domains: DevelopmentalDomains = Field(default_factory=DevelopmentalDomains)

    # === 5. HISTORY (what came before) ===
    history: ChildHistory = Field(default_factory=ChildHistory)

    # Legacy field for backward compatibility
    developmental_history: Optional[str] = None  # old narrative field

    # === 6. FAMILY (who surrounds them) ===
    family: Family = Field(default_factory=Family)

    # Legacy field for backward compatibility
    family_context: Optional[str] = None  # old narrative field

    # === 7. CONCERNS (in context of everything above) ===
    primary_concerns: List[str] = Field(default_factory=list)
    concern_details: Optional[str] = None
    concern_context: Optional[str] = None  # when noticed, triggers, etc.

    # === 8. LIVING EDGE (patterns, hypotheses, questions) ===
    living_edge: LivingEdge = Field(default_factory=LivingEdge)

    # === 9. EXPLORATION ACTIVITY (video cycles, syntheses) ===
    exploration: ExplorationActivity = Field(default_factory=ExplorationActivity)

    # === 10. CURRENT FOCUS (what's active now) ===
    current_focus: CurrentFocus = Field(default_factory=CurrentFocus)

    # === Other context ===
    daily_routines: Optional[str] = None
    parent_goals: Optional[str] = None
    parent_emotional_state: Optional[str] = None  # how parent is coping

    # === Flags ===
    urgent_flags: List[str] = Field(default_factory=list)

    # === Parent preferences ===
    filming_preference: Optional[str] = None  # "wants_videos" | "report_only" | None

    # === Metadata ===
    last_updated: datetime = Field(default_factory=datetime.now)
    extraction_count: int = 0

    @validator('child_name')
    def validate_child_name(cls, v):
        """Reject placeholder values and invalid names"""
        if v is None:
            return None

        placeholders = [
            'unknown', 'not mentioned', 'null', 'none',
            'לא צוין', 'לא ידוע', 'לא נמסר',
            '(not mentioned yet)', '(unknown)',
            'not specified', 'n/a', 'na'
        ]

        if v.lower().strip() in placeholders:
            return None

        if len(v.strip()) < 2:
            return None

        # Reject gibberish
        cleaned = v.strip()
        alpha_chars = sum(1 for c in cleaned if c.isalpha())
        if alpha_chars == 0 or (len(cleaned) > 0 and alpha_chars / len(cleaned) < 0.5):
            return None

        return cleaned

    @validator('age')
    def validate_age(cls, v):
        """Ensure age is valid for child development (0-18 years)"""
        if v is None:
            return None
        if v < 0 or v > 18:
            return None
        return v

    @validator('gender')
    def validate_gender(cls, v):
        """Ensure gender is valid"""
        if v is None:
            return None
        valid_genders = ['male', 'female', 'unknown']
        if v.lower() not in valid_genders:
            return 'unknown'
        return v.lower()

    @validator('primary_concerns')
    def validate_primary_concerns(cls, v):
        """Ensure concerns are from valid set"""
        if not v:
            return []

        valid_concerns = [
            'speech', 'social', 'attention', 'motor', 'sensory',
            'emotional', 'behavioral', 'learning', 'sleep', 'eating', 'other'
        ]

        validated = [c.lower() for c in v if c.lower() in valid_concerns]

        # Reject 'other' as sole concern
        if validated == ['other']:
            return []

        return validated


class Child(BaseModel):
    """
    The Child - the invariant core entity.

    Everything in Chitta orbits around the child. This model contains:
    - Profile and developmental data (extracted from conversations)
    - Artifacts (generated reports, guidelines, analyses)
    - Videos (behavioral observations)
    - Journal (extracted meaningful moments from conversations)

    This data is shared across all users with access to this child.
    """
    child_id: str = Field(description="Unique identifier for the child")

    # Developmental understanding (evolves over time)
    developmental_data: DevelopmentalData = Field(default_factory=DevelopmentalData)

    # Generated artifacts (reports, guidelines, analyses)
    artifacts: Dict[str, Artifact] = Field(
        default_factory=dict,
        description="Generated artifacts keyed by artifact_id"
    )

    # Behavioral observation videos
    videos: List[Video] = Field(default_factory=list)

    # Journal entries (extracted from conversations)
    journal_entries: List[JournalEntry] = Field(default_factory=list)

    # Completeness tracking
    data_completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How much we know about this child (0-1)"
    )

    # LLM quality assessment
    semantic_verification: Optional[Dict[str, Any]] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # === Convenience properties ===

    @property
    def name(self) -> Optional[str]:
        """Child's name for easy access"""
        return self.developmental_data.child_name

    @property
    def age(self) -> Optional[float]:
        """Child's age for easy access"""
        return self.developmental_data.age

    @property
    def profile_summary(self) -> str:
        """Brief profile for display"""
        parts = []
        if self.name:
            parts.append(self.name)
        if self.age:
            parts.append(f"גיל {self.age}")
        return " ".join(parts) if parts else "ילד/ה חדש/ה"

    # === Artifact management ===

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID"""
        return self.artifacts.get(artifact_id)

    def has_artifact(self, artifact_id: str) -> bool:
        """Check if artifact exists and is ready"""
        artifact = self.get_artifact(artifact_id)
        return artifact is not None and artifact.is_ready

    def add_artifact(self, artifact: Artifact):
        """Add or update an artifact"""
        self.artifacts[artifact.artifact_id] = artifact
        self.updated_at = datetime.now()

    # === Video management ===

    def add_video(self, video: Video):
        """Add a video observation"""
        self.videos.append(video)
        self.updated_at = datetime.now()

    def get_video(self, video_id: str) -> Optional[Video]:
        """Get video by ID"""
        return next((v for v in self.videos if v.id == video_id), None)

    def get_videos_pending_analysis(self) -> List[Video]:
        """Get videos that need analysis"""
        return [v for v in self.videos if v.analysis_status == "pending"]

    def get_analyzed_videos(self) -> List[Video]:
        """Get videos with completed analysis"""
        return [v for v in self.videos if v.analysis_status == "ready"]

    @property
    def video_count(self) -> int:
        """Total video count"""
        return len(self.videos)

    @property
    def analyzed_video_count(self) -> int:
        """Count of analyzed videos"""
        return len(self.get_analyzed_videos())

    # === Journal management ===

    def add_journal_entry(self, entry: JournalEntry):
        """Add a journal entry"""
        self.journal_entries.append(entry)
        self.updated_at = datetime.now()

    def get_recent_journal_entries(self, limit: int = 10) -> List[JournalEntry]:
        """Get most recent journal entries"""
        sorted_entries = sorted(
            self.journal_entries,
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_entries[:limit]
