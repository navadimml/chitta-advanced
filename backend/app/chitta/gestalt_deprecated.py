"""
Gestalt Builder - Creates holistic child understanding for Chitta

The Gestalt is the LIVING UNDERSTANDING of a child - not just data, but
insight, hypotheses, patterns, and open questions.

The Gestalt is used by:
1. System prompt - to give Chitta context about the child
2. Tools - to decide what actions are appropriate
3. Hallucination prevention - to verify claims against actual data
4. Guiding conversation - what to explore next

Design principles:
- Child-first, not problem-first
- Strengths before concerns
- Patterns and hypotheses drive exploration
- Honest uncertainty - what we know vs. what we're wondering
- Complete picture - history, family, all domains

The Seven Components:
1. Essence - who is this child?
2. Strengths - what do they do well?
3. Developmental Picture - all domains, not just concerns
4. Context - history, family, environment
5. Concerns - in context of everything above
6. Patterns - themes across observations
7. Hypotheses & Questions - the living edge
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.models.child import Child
from app.models.understanding import (
    DevelopmentalUnderstanding, Hypothesis, Pattern, Evidence, PendingInsight
)
from app.models.exploration import (
    ExplorationCycle, CycleArtifact, VideoScenario,
    ConversationMethod, VideoMethod
)
from app.models.user_session import UserSession


@dataclass
class GestaltIdentity:
    """Child's basic identity - the essentials"""
    name: Optional[str] = None
    age: Optional[float] = None
    gender: Optional[str] = None

    @property
    def is_known(self) -> bool:
        return self.name is not None and self.age is not None

    @property
    def essentials_complete(self) -> bool:
        """Name and age are essential - gender is optional"""
        return self.name is not None and self.age is not None


@dataclass
class GestaltEssence:
    """
    Who is this child as a person - beyond demographics.

    Temperament, energy, core qualities.
    """
    temperament_observations: List[str] = field(default_factory=list)
    energy_pattern: Optional[str] = None
    core_qualities: List[str] = field(default_factory=list)

    @property
    def is_emerging(self) -> bool:
        """Do we have any sense of who this child is?"""
        return bool(self.temperament_observations or self.core_qualities)


@dataclass
class GestaltStrengths:
    """
    What this child does well - elevated to first-class status.

    Strengths are not afterthoughts. They reveal capacity,
    provide intervention pathways, and contextualize difficulties.
    """
    abilities: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    what_lights_them_up: Optional[str] = None
    surprises_people: Optional[str] = None

    @property
    def has_strengths(self) -> bool:
        return bool(self.abilities or self.interests or self.what_lights_them_up)

    @property
    def has_interests(self) -> bool:
        return bool(self.interests)


@dataclass
class GestaltDevelopmentalPicture:
    """
    The full developmental landscape - not just concerns.

    Tracks observations across all domains, both strengths and struggles.
    """
    # Count of observations per domain (for prompt - not full content)
    language_observations: int = 0
    social_emotional_observations: int = 0
    cognitive_observations: int = 0
    motor_observations: int = 0
    sensory_observations: int = 0
    play_observations: int = 0
    adaptive_observations: int = 0

    # Summary of what we know (for prompt)
    domain_summaries: Dict[str, str] = field(default_factory=dict)

    @property
    def has_observations(self) -> bool:
        return any([
            self.language_observations,
            self.social_emotional_observations,
            self.cognitive_observations,
            self.motor_observations,
            self.sensory_observations,
            self.play_observations,
            self.adaptive_observations,
        ])


@dataclass
class GestaltHistory:
    """
    What happened before we met - critical for interpretation.

    A 32-week preemie at age 3 is developmentally different
    from a full-term 3-year-old.
    """
    # Birth
    has_birth_info: bool = False
    was_premature: Optional[bool] = None
    birth_complications: Optional[str] = None

    # Development
    has_milestone_info: bool = False
    milestone_summary: Optional[str] = None

    # Previous evaluations and diagnoses
    has_previous_evaluations: bool = False
    previous_diagnoses: List[str] = field(default_factory=list)
    evaluation_summary: Optional[str] = None

    # Interventions
    has_interventions: bool = False
    intervention_summary: Optional[str] = None


@dataclass
class GestaltFamily:
    """
    Family context - who surrounds this child.

    "Sister speaks for him" changes how we interpret speech delay.
    """
    structure: Optional[str] = None  # "two parents, older sister"
    has_siblings: bool = False
    sibling_dynamics: Optional[str] = None  # relevant notes
    languages_at_home: List[str] = field(default_factory=list)
    family_developmental_history: Optional[str] = None  # "dad was late talker"
    support_system: Optional[str] = None

    @property
    def is_known(self) -> bool:
        return self.structure is not None


@dataclass
class GestaltConcerns:
    """What brought them here - in context of everything else"""
    primary_areas: List[str] = field(default_factory=list)
    details: Optional[str] = None
    context: Optional[str] = None  # when noticed, triggers
    urgent_flags: List[str] = field(default_factory=list)

    @property
    def has_concerns(self) -> bool:
        return len(self.primary_areas) > 0

    @property
    def has_details(self) -> bool:
        return bool(self.details)


@dataclass
class GestaltPatterns:
    """
    Patterns detected across observations.

    Patterns are themes that appear repeatedly:
    - "Mornings hard" + "car seat battles" + "bedtime struggles"
      = "Transitions are difficult"
    """
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {theme, observations, confidence}

    @property
    def has_patterns(self) -> bool:
        return len(self.patterns) > 0


@dataclass
class GestaltHypotheses:
    """
    Working theories - held lightly, open to revision.

    Not "Daniel has autism" but "Daniel's speech delay might be
    primarily temperament-related - capacity is there, safety is the key."

    Each hypothesis includes:
    - id: Unique identifier for linking evidence
    - theory: The working hypothesis
    - domain: Developmental domain (sensory, motor, social, etc.)
    - confidence: 0-1, changes with evidence
    - status: forming, active, weakening, resolved
    - evidence_count: How many pieces of evidence
    - questions_to_explore: Questions that would test this hypothesis
    """
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {id, theory, domain, confidence, status, evidence_count, questions_to_explore}

    @property
    def has_hypotheses(self) -> bool:
        return len(self.hypotheses) > 0

    @property
    def active_hypotheses(self) -> List[Dict[str, Any]]:
        """Get hypotheses that are still being explored (forming or active)."""
        return [h for h in self.hypotheses if h.get("status") in ["forming", "active"]]

    @property
    def resolved_hypotheses(self) -> List[Dict[str, Any]]:
        """Get hypotheses that have been resolved."""
        return [h for h in self.hypotheses if h.get("status") == "resolved"]


@dataclass
class GestaltOpenQuestions:
    """
    What we're still wondering about.

    Open questions keep the Gestalt alive and drive curiosity.
    """
    questions: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {question, arose_from, priority}

    contradictions: List[str] = field(default_factory=list)
    # Things that don't fit: "Usually cautious but spontaneous with grandma"

    @property
    def has_questions(self) -> bool:
        return len(self.questions) > 0 or len(self.contradictions) > 0


@dataclass
class GestaltStories:
    """Stories captured from conversation - these are gold."""
    story_count: int = 0
    recent_stories: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {content, themes, sentiment, what_it_reveals}


@dataclass
class GestaltObservations:
    """
    Video and story observations state.

    Tracks what has been observed through videos and how much has been analyzed.
    """
    # === Video Counts ===
    video_count: int = 0  # Total videos uploaded
    pending_video_count: int = 0  # Videos awaiting analysis
    analyzed_video_count: int = 0  # Videos that have been analyzed

    # === Recent Content ===
    recent_stories: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {content, themes, sentiment, what_it_reveals}

    @property
    def has_pending_videos(self) -> bool:
        return self.pending_video_count > 0

    @property
    def has_videos(self) -> bool:
        return self.video_count > 0


@dataclass
class GestaltExploration:
    """
    Current exploration state - unified across conversation and video.

    Tracks what we're actively exploring, regardless of method.
    """
    # === Current Cycle ===
    has_active_cycle: bool = False
    current_cycle_id: Optional[str] = None
    current_cycle_started: Optional[datetime] = None
    exploration_goal: Optional[str] = None  # What we're trying to understand

    # === Methods Being Used ===
    methods_used: List[str] = field(default_factory=list)  # ["conversation", "video"]

    # === Purpose: What We're Exploring ===
    hypotheses_being_tested: List[str] = field(default_factory=list)
    questions_being_explored: List[str] = field(default_factory=list)

    # === Conversation Method State ===
    pending_questions: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {question, what_we_hoped_to_learn, target_hypothesis}

    # === Video Method State ===
    pending_video_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {scenario, why_we_want_to_see, requested_at}
    pending_video_analyses: List[str] = field(default_factory=list)

    # === What's New (needs discussion) ===
    new_videos_not_discussed: List[str] = field(default_factory=list)
    new_analyses_not_discussed: List[str] = field(default_factory=list)
    new_evidence_not_discussed: List[str] = field(default_factory=list)

    # === History Summary ===
    completed_cycles_count: int = 0
    total_videos_analyzed: int = 0
    total_evidence_items: int = 0

    @property
    def is_waiting(self) -> bool:
        """Are we waiting for anything?"""
        return (len(self.pending_questions) > 0 or
                len(self.pending_video_scenarios) > 0 or
                len(self.pending_video_analyses) > 0)

    @property
    def is_waiting_for_videos(self) -> bool:
        return len(self.pending_video_scenarios) > 0

    @property
    def has_new_content(self) -> bool:
        return bool(self.new_videos_not_discussed or
                    self.new_analyses_not_discussed or
                    self.new_evidence_not_discussed)

    @property
    def uses_video(self) -> bool:
        return "video" in self.methods_used

    @property
    def uses_conversation(self) -> bool:
        return "conversation" in self.methods_used


@dataclass
class GestaltSyntheses:
    """
    Synthesis state - reports/summaries over time.

    This replaces "has_parent_report" boolean with temporal awareness.
    """
    # === Current State ===
    has_current_synthesis: bool = False
    current_synthesis_id: Optional[str] = None
    current_synthesis_date: Optional[datetime] = None

    # === Freshness ===
    days_since_last_synthesis: Optional[int] = None
    significant_changes_since: List[str] = field(default_factory=list)
    synthesis_might_be_outdated: bool = False

    # === History ===
    total_syntheses_count: int = 0

    # === New and Unread ===
    new_syntheses_not_discussed: List[str] = field(default_factory=list)


@dataclass
class GestaltSession:
    """Current session state - includes returning user context"""
    turn_count: int = 0
    message_count: int = 0
    is_returning: bool = False

    # Returning user context
    time_since_last: Optional[timedelta] = None
    last_session_emotional_state: Optional[str] = None

    # Pending items
    pending_videos: int = 0
    pending_analyses: int = 0
    new_artifacts_unseen: List[str] = field(default_factory=list)

    # Open threads from previous session
    open_threads: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {topic, status, last_discussed, notes}

    # Active UI cards
    active_card_ids: List[str] = field(default_factory=list)


@dataclass
class GestaltCompleteness:
    """
    How complete is our understanding - expanded tracking.

    Not just a score, but specific gaps we need to fill.
    """
    score: float = 0.0  # 0-1

    # What's missing
    missing_essentials: List[str] = field(default_factory=list)  # name, age
    missing_strengths: bool = True
    missing_essence: bool = True
    missing_history: List[str] = field(default_factory=list)  # birth, milestones, etc.
    missing_family: List[str] = field(default_factory=list)  # structure, siblings, etc.
    missing_domains: List[str] = field(default_factory=list)  # developmental areas

    @property
    def level(self) -> str:
        """Completeness level for prompt guidance"""
        if self.score < 0.2:
            return "initial"
        elif self.score < 0.4:
            return "early"
        elif self.score < 0.6:
            return "developing"
        elif self.score < 0.8:
            return "good"
        else:
            return "rich"

    @property
    def needs_essentials(self) -> bool:
        return len(self.missing_essentials) > 0

    @property
    def needs_strengths(self) -> bool:
        return self.missing_strengths


@dataclass
class GestaltArtifacts:
    """
    Artifacts state - derived from exploration cycles.

    In the new model, artifacts belong to exploration cycles.
    This class provides a convenience view for checking artifact availability.
    """
    # Video guidelines (from any cycle)
    has_video_guidelines: bool = False
    guidelines_artifact_id: Optional[str] = None
    guidelines_cycle_id: Optional[str] = None

    # Parent report / synthesis (from any cycle)
    has_parent_report: bool = False
    report_artifact_id: Optional[str] = None
    report_cycle_id: Optional[str] = None

    # All artifact IDs for quick lookup
    all_artifact_ids: List[str] = field(default_factory=list)

    def available_artifacts(self) -> List[str]:
        """Return list of available artifact types."""
        available = []
        if self.has_video_guidelines:
            available.append("video_guidelines")
        if self.has_parent_report:
            available.append("parent_report")
        return available


@dataclass
class Gestalt:
    """
    The Living Gestalt - everything we know AND are wondering about a child.

    This is the PRIMARY context Chitta uses for all decisions.

    Structure follows the Living Gestalt philosophy:
    1. Identity (name, age, gender)
    2. Essence (who they are)
    3. Strengths (what they do well) - FIRST CLASS
    4. Developmental picture (all domains)
    5. History (what came before)
    6. Family (who surrounds them)
    7. Concerns (in context)
    8. Patterns (themes across observations)
    9. Hypotheses (working theories)
    10. Open questions (what we're wondering)

    Activity tracking (not state-based):
    - Exploration cycles (unified - conversation/video/mixed)
    - Synthesis snapshots (temporal, not boolean)
    - Current focus (what's active NOW)
    """
    child_id: str

    # === The Seven Components ===
    identity: GestaltIdentity = field(default_factory=GestaltIdentity)
    essence: GestaltEssence = field(default_factory=GestaltEssence)
    strengths: GestaltStrengths = field(default_factory=GestaltStrengths)
    developmental_picture: GestaltDevelopmentalPicture = field(default_factory=GestaltDevelopmentalPicture)
    history: GestaltHistory = field(default_factory=GestaltHistory)
    family: GestaltFamily = field(default_factory=GestaltFamily)
    concerns: GestaltConcerns = field(default_factory=GestaltConcerns)

    # === The Living Edge ===
    patterns: GestaltPatterns = field(default_factory=GestaltPatterns)
    hypotheses: GestaltHypotheses = field(default_factory=GestaltHypotheses)
    open_questions: GestaltOpenQuestions = field(default_factory=GestaltOpenQuestions)

    # === Stories (gold) ===
    stories: GestaltStories = field(default_factory=GestaltStories)

    # === Observations (videos and stories) ===
    observations: GestaltObservations = field(default_factory=GestaltObservations)

    # === Activity-Based Tracking (unified exploration) ===
    exploration: GestaltExploration = field(default_factory=GestaltExploration)
    syntheses: GestaltSyntheses = field(default_factory=GestaltSyntheses)

    # === Artifacts (derived from exploration cycles) ===
    artifacts: GestaltArtifacts = field(default_factory=GestaltArtifacts)

    # === Session and Completeness ===
    session: GestaltSession = field(default_factory=GestaltSession)
    completeness: GestaltCompleteness = field(default_factory=GestaltCompleteness)

    # === Parent Context ===
    filming_preference: Optional[str] = None
    parent_goals: Optional[str] = None
    parent_emotional_state: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization or prompt building"""
        return {
            "child_id": self.child_id,
            "identity": {
                "name": self.identity.name,
                "age": self.identity.age,
                "gender": self.identity.gender,
                "essentials_complete": self.identity.essentials_complete,
            },
            "essence": {
                "temperament": self.essence.temperament_observations,
                "energy_pattern": self.essence.energy_pattern,
                "core_qualities": self.essence.core_qualities,
                "is_emerging": self.essence.is_emerging,
            },
            "strengths": {
                "abilities": self.strengths.abilities,
                "interests": self.strengths.interests,
                "what_lights_them_up": self.strengths.what_lights_them_up,
                "has_strengths": self.strengths.has_strengths,
            },
            "history": {
                "has_birth_info": self.history.has_birth_info,
                "was_premature": self.history.was_premature,
                "has_previous_evaluations": self.history.has_previous_evaluations,
                "previous_diagnoses": self.history.previous_diagnoses,
            },
            "family": {
                "structure": self.family.structure,
                "has_siblings": self.family.has_siblings,
                "languages": self.family.languages_at_home,
                "family_history": self.family.family_developmental_history,
            },
            "concerns": {
                "primary_areas": self.concerns.primary_areas,
                "details": self.concerns.details,
                "urgent_flags": self.concerns.urgent_flags,
            },
            "patterns": {
                "detected": self.patterns.patterns,
                "has_patterns": self.patterns.has_patterns,
            },
            "hypotheses": {
                "working": self.hypotheses.hypotheses,
                "has_hypotheses": self.hypotheses.has_hypotheses,
            },
            "open_questions": {
                "questions": self.open_questions.questions,
                "contradictions": self.open_questions.contradictions,
            },
            "stories": {
                "count": self.stories.story_count,
                "recent": self.stories.recent_stories,
            },
            "exploration": {
                "has_active_cycle": self.exploration.has_active_cycle,
                "exploration_goal": self.exploration.exploration_goal,
                "methods_used": self.exploration.methods_used,
                "hypotheses_being_tested": self.exploration.hypotheses_being_tested,
                "questions_being_explored": self.exploration.questions_being_explored,
                "pending_questions": self.exploration.pending_questions,
                "pending_video_scenarios": self.exploration.pending_video_scenarios,
                "is_waiting": self.exploration.is_waiting,
                "is_waiting_for_videos": self.exploration.is_waiting_for_videos,
                "has_new_content": self.exploration.has_new_content,
                "completed_cycles_count": self.exploration.completed_cycles_count,
            },
            "syntheses": {
                "has_current_synthesis": self.syntheses.has_current_synthesis,
                "days_since_last": self.syntheses.days_since_last_synthesis,
                "might_be_outdated": self.syntheses.synthesis_might_be_outdated,
                "total_count": self.syntheses.total_syntheses_count,
            },
            "session": {
                "turn_count": self.session.turn_count,
                "is_returning": self.session.is_returning,
                "time_since_last": str(self.session.time_since_last) if self.session.time_since_last else None,
                "open_threads": self.session.open_threads,
            },
            "completeness": {
                "score": self.completeness.score,
                "level": self.completeness.level,
                "missing_essentials": self.completeness.missing_essentials,
                "missing_strengths": self.completeness.missing_strengths,
                "missing_history": self.completeness.missing_history,
                "missing_family": self.completeness.missing_family,
            },
            "filming_preference": self.filming_preference,
            "parent_goals": self.parent_goals,
        }


def build_gestalt(child: Child, session: UserSession) -> Gestalt:
    """
    Build a Living Gestalt from Child and UserSession data.

    This transforms persisted data into the session view that Chitta uses.
    The structure follows the Living Gestalt philosophy:
    1. Identity (essentials first)
    2. Essence (who they are)
    3. Strengths (elevated, not afterthought)
    4. History, Family, Context
    5. Concerns (in context of everything above)
    6. Patterns, Hypotheses, Questions (the living edge)
    """
    # Use new Child model attributes directly (not backward-compat developmental_data)

    # === 1. IDENTITY ===
    identity = GestaltIdentity(
        name=child.identity.name,
        age=child.identity.age_years,
        gender=child.identity.gender,
    )

    # === 2. ESSENCE ===
    essence = GestaltEssence(
        temperament_observations=child.essence.temperament_observations,
        energy_pattern=child.essence.energy_pattern,
        core_qualities=child.essence.core_qualities,
    )

    # === 3. STRENGTHS ===
    strengths = GestaltStrengths(
        abilities=child.strengths.abilities,
        interests=child.strengths.interests,
        what_lights_them_up=child.strengths.what_lights_them_up,
        surprises_people=child.strengths.surprises_people,
    )

    # === 4. DEVELOPMENTAL PICTURE ===
    # Count observations from understanding patterns
    understanding = child.understanding
    developmental_picture = GestaltDevelopmentalPicture(
        language_observations=_count_domain_observations(understanding, "language"),
        social_emotional_observations=_count_domain_observations(understanding, "social"),
        cognitive_observations=_count_domain_observations(understanding, "cognitive"),
        motor_observations=_count_domain_observations(understanding, "motor"),
        sensory_observations=_count_domain_observations(understanding, "sensory"),
        play_observations=_count_domain_observations(understanding, "play"),
        adaptive_observations=_count_domain_observations(understanding, "adaptive"),
    )

    # === 5. HISTORY ===
    hist = child.history
    history = GestaltHistory(
        has_birth_info=bool(hist.birth.complications or hist.birth.premature is not None),
        was_premature=hist.birth.premature,
        birth_complications=hist.birth.complications,
        has_milestone_info=bool(hist.milestone_notes or hist.early_development),
        milestone_summary=hist.milestone_notes or hist.early_development,
        has_previous_evaluations=len(hist.previous_evaluations) > 0,
        previous_diagnoses=hist.previous_diagnoses,
        has_interventions=False,  # DevelopmentalHistory doesn't have interventions field
    )

    # === 6. FAMILY ===
    fam = child.family
    family = GestaltFamily(
        structure=fam.structure,
        has_siblings=len(fam.siblings) > 0,
        sibling_dynamics=_get_sibling_dynamics(fam.siblings) if fam.siblings else None,
        languages_at_home=fam.languages_at_home,
        family_developmental_history=fam.family_developmental_history,
        support_system=fam.support_system,
    )

    # === 7. CONCERNS ===
    # Get context from concern details if available
    concern_context = None
    if child.concerns.details:
        examples = child.concerns.details[0].examples if child.concerns.details[0].examples else []
        concern_context = examples[0] if examples else None

    concerns = GestaltConcerns(
        primary_areas=child.concerns.primary_areas or [],
        details=child.concerns.parent_narrative,
        context=concern_context,
        urgent_flags=[],  # Concerns model doesn't have urgent_flags
    )

    # === 8. PATTERNS ===
    # Use understanding.patterns from the new model
    patterns = GestaltPatterns(
        patterns=[
            {
                "theme": p.theme,
                "observations": [],  # Pattern doesn't have direct observations
                "confidence": p.confidence,
            }
            for p in understanding.patterns
        ]
    )

    # === 9. HYPOTHESES ===
    # Build rich hypothesis data for LLM context
    hypotheses = GestaltHypotheses(
        hypotheses=[
            {
                "id": h.id,
                "theory": h.theory,
                "domain": h.domain,
                "confidence": h.confidence,
                "status": h.status,
                "evidence_count": len(h.evidence),
                "supporting_count": sum(1 for e in h.evidence if "supports" in str(getattr(e, 'effect', ''))),
                "contradicting_count": sum(1 for e in h.evidence if "contradicts" in str(getattr(e, 'effect', ''))),
                "last_evidence_at": h.last_evidence_at.isoformat() if h.last_evidence_at else None,
                "resolution": h.resolution,
                "resolution_note": h.resolution_note,
                "evolved_into": h.evolved_into,
                # Questions that would test this hypothesis (from form_hypothesis)
                "questions_to_explore": getattr(h, 'questions_to_explore', []),
            }
            for h in understanding.hypotheses
        ]
    )

    # === 10. OPEN QUESTIONS ===
    # DevelopmentalUnderstanding doesn't have open_questions directly
    # They would need to be tracked separately or derived from hypotheses
    open_questions = GestaltOpenQuestions(
        questions=[],
        contradictions=[],
    )

    # === STORIES ===
    recent_stories = []
    for entry in child.recent_journal_entries(5):
        recent_stories.append({
            "content": entry.content,
            "themes": entry.themes,
            "sentiment": None,  # JournalEntry doesn't have sentiment
        })
    stories = GestaltStories(
        story_count=len(child.journal_entries),
        recent_stories=recent_stories,
    )

    # === OBSERVATIONS (videos and stories) ===
    total_videos = len(child.videos)
    analyzed_videos = len(child.analyzed_videos())
    pending_videos = total_videos - analyzed_videos

    observations = GestaltObservations(
        video_count=total_videos,
        pending_video_count=pending_videos,
        analyzed_video_count=analyzed_videos,
        recent_stories=recent_stories,  # Share with stories for consistency
    )

    # === EXPLORATION (from exploration_cycles list) ===
    active_cycles = child.active_exploration_cycles()
    current_cycle = active_cycles[0] if active_cycles else None

    # Build pending questions from conversation method
    pending_questions = []
    if current_cycle and current_cycle.conversation_method:
        for q in current_cycle.conversation_method.questions:
            if not q.answered:
                pending_questions.append({
                    "question": q.question,
                    "what_we_hoped_to_learn": None,
                    "target_hypothesis": None,
                })

    # Build pending video scenarios from video method
    pending_video_scenarios = []
    if current_cycle and current_cycle.video_method:
        for s in current_cycle.video_method.scenarios:
            if not s.uploaded:
                pending_video_scenarios.append({
                    "scenario": s.title,
                    "why_we_want_to_see": s.what_we_hope_to_learn,
                    "requested_at": None,
                })

    # Count completed cycles and determine methods used
    completed_count = len([c for c in child.exploration_cycles if c.status == "complete"])
    methods_used = []
    questions_being_explored = []
    if current_cycle:
        if current_cycle.conversation_method:
            methods_used.append("conversation")
            # Extract question strings from conversation method
            questions_being_explored = [
                q.question for q in current_cycle.conversation_method.questions
            ]
        if current_cycle.video_method:
            methods_used.append("video")

    exploration = GestaltExploration(
        has_active_cycle=len(active_cycles) > 0,
        current_cycle_id=current_cycle.id if current_cycle else None,
        current_cycle_started=current_cycle.created_at if current_cycle else None,
        exploration_goal=current_cycle.focus_description if current_cycle else None,
        methods_used=methods_used,
        hypotheses_being_tested=current_cycle.hypothesis_ids if current_cycle else [],
        questions_being_explored=questions_being_explored,
        pending_questions=pending_questions,
        pending_video_scenarios=pending_video_scenarios,
        pending_video_analyses=[v.id for v in child.videos if v.analysis_status == "analyzing"],
        new_videos_not_discussed=[],
        new_analyses_not_discussed=[],
        completed_cycles_count=completed_count,
        total_videos_analyzed=len(child.analyzed_videos()),
    )

    # === SYNTHESES ===
    # Look for synthesis reports in exploration cycles
    synthesis_artifacts = []
    for cycle in child.exploration_cycles:
        for artifact in cycle.artifacts:
            if artifact.type == "synthesis_report":
                synthesis_artifacts.append(artifact)
    current_synthesis = synthesis_artifacts[-1] if synthesis_artifacts else None

    syntheses = GestaltSyntheses(
        has_current_synthesis=current_synthesis is not None,
        current_synthesis_id=current_synthesis.id if current_synthesis else None,
        current_synthesis_date=current_synthesis.created_at if current_synthesis else None,
        days_since_last_synthesis=None,
        significant_changes_since=[],
        synthesis_might_be_outdated=False,
        total_syntheses_count=len(synthesis_artifacts),
        new_syntheses_not_discussed=[],
    )

    # === SESSION ===
    session_info = GestaltSession(
        turn_count=session.turn_count,
        message_count=session.message_count,
        is_returning=session.message_count > 0,
        time_since_last=None,
        last_session_emotional_state=None,
        open_threads=[],
        active_card_ids=[card.card_id for card in session.active_cards],
    )

    # === COMPLETENESS ===
    completeness = _calculate_completeness_from_child(child)

    # === ARTIFACTS (derived from exploration cycles) ===
    artifacts = _build_artifacts_from_cycles(child)

    return Gestalt(
        child_id=child.id,
        identity=identity,
        essence=essence,
        strengths=strengths,
        developmental_picture=developmental_picture,
        history=history,
        family=family,
        concerns=concerns,
        patterns=patterns,
        hypotheses=hypotheses,
        open_questions=open_questions,
        stories=stories,
        observations=observations,
        exploration=exploration,
        syntheses=syntheses,
        artifacts=artifacts,
        session=session_info,
        completeness=completeness,
        filming_preference=None,
        parent_goals=None,
        parent_emotional_state=None,
    )


def _get_sibling_dynamics(siblings: List) -> Optional[str]:
    """Extract relevant sibling dynamics for prompt."""
    dynamics = []
    for sibling in siblings:
        if sibling.notes:
            dynamics.append(sibling.notes)
    return "; ".join(dynamics) if dynamics else None


def _build_artifacts_from_cycles(child: Child) -> GestaltArtifacts:
    """
    Build artifacts state by scanning all exploration cycles.

    Artifacts now live inside cycles, so we need to scan all cycles
    to determine what artifacts are available.
    """
    has_video_guidelines = False
    guidelines_artifact_id = None
    guidelines_cycle_id = None

    has_parent_report = False
    report_artifact_id = None
    report_cycle_id = None

    all_artifact_ids = []

    # Scan all cycles for artifacts
    for cycle in child.exploration_cycles:
        for artifact in cycle.artifacts:
            all_artifact_ids.append(artifact.id)

            # Check for video guidelines (any status except superseded)
            if artifact.type == "video_guidelines" and artifact.status != "superseded":
                has_video_guidelines = True
                guidelines_artifact_id = artifact.id
                guidelines_cycle_id = cycle.id

            # Check for synthesis report / parent report
            if artifact.type in ["synthesis_report", "parent_report"] and artifact.status == "ready":
                has_parent_report = True
                report_artifact_id = artifact.id
                report_cycle_id = cycle.id

    return GestaltArtifacts(
        has_video_guidelines=has_video_guidelines,
        guidelines_artifact_id=guidelines_artifact_id,
        guidelines_cycle_id=guidelines_cycle_id,
        has_parent_report=has_parent_report,
        report_artifact_id=report_artifact_id,
        report_cycle_id=report_cycle_id,
        all_artifact_ids=all_artifact_ids,
    )


def _count_domain_observations(understanding: DevelopmentalUnderstanding, domain: str) -> int:
    """
    Count observations for a specific developmental domain.

    Counts evidence across all hypotheses in that domain.
    """
    count = 0
    for hypothesis in understanding.hypotheses:
        if hypothesis.domain == domain or domain in hypothesis.domain:
            count += len(hypothesis.evidence)
    return count


def _calculate_completeness_from_child(child: Child) -> GestaltCompleteness:
    """
    Calculate completeness using the new Child model directly.

    Weights (approximate):
    - Essentials (name, age): 15%
    - Strengths: 15%
    - Essence: 10%
    - History: 15%
    - Family: 10%
    - Concerns: 15%
    - Observations: 10%
    - Living edge (patterns/hypotheses): 10%
    """
    score = 0.0

    # Essentials (15%)
    missing_essentials = []
    if not child.identity.name:
        missing_essentials.append("name")
    else:
        score += 0.075
    if not child.identity.age_years:
        missing_essentials.append("age")
    else:
        score += 0.075

    # Strengths (15%)
    missing_strengths = not (
        child.strengths.abilities or
        child.strengths.interests or
        child.strengths.what_lights_them_up
    )
    if not missing_strengths:
        score += 0.15

    # Essence (10%)
    missing_essence = not (
        child.essence.temperament_observations or
        child.essence.core_qualities
    )
    if not missing_essence:
        score += 0.10

    # History (15%)
    missing_history = []
    if not (child.history.birth.complications or child.history.birth.premature is not None):
        missing_history.append("birth")
    else:
        score += 0.05
    if not child.history.milestone_notes:
        missing_history.append("milestones")
    else:
        score += 0.05
    if not child.history.previous_evaluations and not child.history.previous_diagnoses:
        missing_history.append("previous_evaluations")
    else:
        score += 0.05

    # Family (10%)
    missing_family = []
    if not child.family.structure:
        missing_family.append("structure")
    else:
        score += 0.05
    if not child.family.languages_at_home:
        missing_family.append("languages")
    else:
        score += 0.025
    if not child.family.family_developmental_history:
        missing_family.append("family_history")
    else:
        score += 0.025

    # Concerns (15%)
    if child.concerns.primary_areas:
        score += 0.075
    if child.concerns.parent_narrative:
        score += 0.075

    # Observations (10%)
    if len(child.journal_entries) > 0:
        score += 0.05
    if child.video_count > 0:
        score += 0.05

    # Living edge (10%)
    if child.understanding.patterns:
        score += 0.05
    if child.understanding.hypotheses:
        score += 0.05

    return GestaltCompleteness(
        score=min(score, 1.0),
        missing_essentials=missing_essentials,
        missing_strengths=missing_strengths,
        missing_essence=missing_essence,
        missing_history=missing_history,
        missing_family=missing_family,
    )


def get_what_we_know(gestalt: Gestalt) -> Dict[str, Any]:
    """
    Get a summary of what we actually know (for hallucination prevention).

    Returns only fields that have actual values.
    Organized by the Living Gestalt components.
    """
    known = {}

    # Identity
    if gestalt.identity.name:
        known["child_name"] = gestalt.identity.name
    if gestalt.identity.age:
        known["age"] = gestalt.identity.age
    if gestalt.identity.gender and gestalt.identity.gender != "unknown":
        known["gender"] = gestalt.identity.gender

    # Essence
    if gestalt.essence.is_emerging:
        known["essence"] = {
            "temperament": gestalt.essence.temperament_observations,
            "qualities": gestalt.essence.core_qualities,
        }

    # Strengths
    if gestalt.strengths.has_strengths:
        known["strengths"] = {
            "abilities": gestalt.strengths.abilities,
            "interests": gestalt.strengths.interests,
            "what_lights_them_up": gestalt.strengths.what_lights_them_up,
        }

    # History
    if gestalt.history.has_birth_info:
        known["birth_history"] = {
            "premature": gestalt.history.was_premature,
            "complications": gestalt.history.birth_complications,
        }
    if gestalt.history.previous_diagnoses:
        known["previous_diagnoses"] = gestalt.history.previous_diagnoses

    # Family
    if gestalt.family.is_known:
        known["family"] = {
            "structure": gestalt.family.structure,
            "languages": gestalt.family.languages_at_home,
            "family_history": gestalt.family.family_developmental_history,
        }

    # Concerns
    if gestalt.concerns.primary_areas:
        known["concerns"] = gestalt.concerns.primary_areas
    if gestalt.concerns.details:
        known["concern_details"] = gestalt.concerns.details

    # Patterns
    if gestalt.patterns.has_patterns:
        known["patterns"] = [p["theme"] for p in gestalt.patterns.patterns]

    # Hypotheses - include status so LLM knows which are active
    if gestalt.hypotheses.has_hypotheses:
        known["hypotheses"] = [
            {
                "id": h.get("id", ""),
                "theory": h["theory"],
                "status": h.get("status", "active"),
                "confidence": h.get("confidence", 0.5),
            }
            for h in gestalt.hypotheses.hypotheses
        ]

    # Stories
    if gestalt.stories.story_count > 0:
        known["stories_captured"] = gestalt.stories.story_count

    # Exploration (unified - conversation/video/mixed)
    if gestalt.exploration.has_active_cycle:
        known["exploration"] = {
            "goal": gestalt.exploration.exploration_goal,
            "methods": gestalt.exploration.methods_used,
            "hypotheses_being_tested": gestalt.exploration.hypotheses_being_tested,
            "questions_being_explored": gestalt.exploration.questions_being_explored,
            "is_waiting": gestalt.exploration.is_waiting,
            "waiting_for_videos": gestalt.exploration.is_waiting_for_videos,
            "pending_questions_count": len(gestalt.exploration.pending_questions),
            "pending_video_scenarios_count": len(gestalt.exploration.pending_video_scenarios),
        }
    if gestalt.exploration.total_videos_analyzed > 0:
        known["videos_analyzed"] = gestalt.exploration.total_videos_analyzed
    if gestalt.exploration.completed_cycles_count > 0:
        known["completed_exploration_cycles"] = gestalt.exploration.completed_cycles_count

    # Syntheses (activity-based)
    if gestalt.syntheses.has_current_synthesis:
        known["current_synthesis"] = {
            "days_since": gestalt.syntheses.days_since_last_synthesis,
            "might_be_outdated": gestalt.syntheses.synthesis_might_be_outdated,
        }

    return known


def get_what_we_need(gestalt: Gestalt) -> List[str]:
    """
    Get a prioritized list of what information we still need.

    Priority order (following Living Gestalt):
    1. Essentials (name, age)
    2. Strengths (before concerns!)
    3. Context (history, family)
    4. Concerns (in context of above)
    5. Observations
    """
    needs = []

    # 1. Essentials first - can't interpret anything without age
    needs.extend(gestalt.completeness.missing_essentials)

    # 2. Strengths - elevated priority
    if gestalt.completeness.missing_strengths:
        needs.append("strengths")

    # 3. Essence
    if gestalt.completeness.missing_essence:
        needs.append("essence")

    # 4. History - critical for interpretation
    for item in gestalt.completeness.missing_history:
        needs.append(f"history_{item}")

    # 5. Family
    for item in gestalt.completeness.missing_family:
        needs.append(f"family_{item}")

    # 6. Concerns (if we don't have them yet)
    if not gestalt.concerns.has_concerns:
        needs.append("primary_concerns")
    elif not gestalt.concerns.has_details:
        needs.append("concern_details")

    # 7. Exploration (if no exploration has happened and we have hypotheses to test)
    if not gestalt.exploration.has_active_cycle and gestalt.exploration.completed_cycles_count == 0:
        if gestalt.hypotheses.has_hypotheses:
            needs.append("exploration_to_test_hypotheses")

    return needs


def get_conversation_priority(gestalt: Gestalt) -> Dict[str, Any]:
    """
    Get guidance for what Chitta should focus on now.

    This returns structured guidance based on the current state
    of the Gestalt, following the Living Gestalt philosophy.
    """
    level = gestalt.completeness.level

    # Determine phase and priority
    if not gestalt.identity.essentials_complete:
        return {
            "phase": "essentials",
            "priority": "Get name and age - foundational for everything",
            "focus": gestalt.completeness.missing_essentials,
            "approach": "natural_opening",
        }

    if gestalt.completeness.missing_strengths:
        return {
            "phase": "strengths",
            "priority": "Learn about strengths - what child loves, does well",
            "focus": ["interests", "abilities", "what_lights_them_up"],
            "approach": "curious_exploration",
        }

    if gestalt.completeness.missing_essence:
        return {
            "phase": "essence",
            "priority": "Understand who this child is as a person",
            "focus": ["temperament", "core_qualities"],
            "approach": "through_stories",
        }

    if gestalt.completeness.missing_history:
        return {
            "phase": "context",
            "priority": "Complete the picture - history matters",
            "focus": gestalt.completeness.missing_history,
            "approach": "natural_questions",
        }

    if not gestalt.concerns.has_concerns:
        return {
            "phase": "concerns",
            "priority": "Understand what brought them here",
            "focus": ["primary_concerns"],
            "approach": "gentle_inquiry",
        }

    if gestalt.concerns.has_concerns and not gestalt.concerns.has_details:
        return {
            "phase": "deep_dive",
            "priority": "Get specific examples of concerns",
            "focus": ["concern_details", "stories"],
            "approach": "story_elicitation",
        }

    if gestalt.patterns.has_patterns or gestalt.hypotheses.has_hypotheses:
        return {
            "phase": "exploration",
            "priority": "Explore patterns and test hypotheses",
            "focus": [h["theory"] for h in gestalt.hypotheses.active_hypotheses],
            "approach": "hypothesis_driven",
        }

    return {
        "phase": "synthesis",
        "priority": "Deepen understanding, offer synthesis",
        "focus": ["maintain_rapport", "offer_artifacts"],
        "approach": "supportive",
    }
