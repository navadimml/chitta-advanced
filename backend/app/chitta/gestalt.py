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

from app.models.child import (
    Child, DevelopmentalData, Essence, Strengths as StrengthsModel,
    DevelopmentalDomains, ChildHistory, Family, LivingEdge,
    Pattern, Hypothesis, OpenQuestion, EvidenceItem,
    ExplorationActivity, ExplorationCycle, SynthesisSnapshot,
    CurrentFocus, VideoScenario, ConversationQuestion,
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
    """
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {theory, supporting, contradicting, status}

    @property
    def has_hypotheses(self) -> bool:
        return len(self.hypotheses) > 0

    @property
    def active_hypotheses(self) -> List[Dict[str, Any]]:
        return [h for h in self.hypotheses if h.get("status") == "exploring"]


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

    # === Activity-Based Tracking (unified exploration) ===
    exploration: GestaltExploration = field(default_factory=GestaltExploration)
    syntheses: GestaltSyntheses = field(default_factory=GestaltSyntheses)

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
    data = child.developmental_data

    # === 1. IDENTITY ===
    identity = GestaltIdentity(
        name=data.child_name,
        age=data.age,
        gender=data.gender,
    )

    # === 2. ESSENCE ===
    essence = GestaltEssence(
        temperament_observations=data.essence.temperament_observations,
        energy_pattern=data.essence.energy_pattern,
        core_qualities=data.essence.core_qualities,
    )

    # === 3. STRENGTHS ===
    strengths = GestaltStrengths(
        abilities=data.strengths.abilities,
        interests=data.strengths.interests,
        what_lights_them_up=data.strengths.what_lights_them_up,
        surprises_people=data.strengths.surprises_people,
    )

    # === 4. DEVELOPMENTAL PICTURE ===
    domains = data.developmental_domains
    developmental_picture = GestaltDevelopmentalPicture(
        language_observations=(
            len(domains.language_receptive) +
            len(domains.language_expressive) +
            len(domains.language_pragmatic)
        ),
        social_emotional_observations=(
            len(domains.social_relationships) +
            len(domains.emotional_regulation) +
            len(domains.social_awareness)
        ),
        cognitive_observations=len(domains.cognitive),
        motor_observations=len(domains.motor_gross) + len(domains.motor_fine),
        sensory_observations=len(domains.sensory_processing),
        play_observations=len(domains.play_and_imagination),
        adaptive_observations=len(domains.adaptive_skills),
    )

    # === 5. HISTORY ===
    hist = data.history
    history = GestaltHistory(
        has_birth_info=bool(hist.birth.complications or hist.birth.premature is not None),
        was_premature=hist.birth.premature,
        birth_complications=hist.birth.complications,
        has_milestone_info=bool(hist.milestone_notes),
        milestone_summary=hist.milestone_notes,
        has_previous_evaluations=len(hist.previous_evaluations) > 0,
        previous_diagnoses=hist.previous_diagnoses,
        has_interventions=len(hist.interventions) > 0,
    )

    # === 6. FAMILY ===
    fam = data.family
    family = GestaltFamily(
        structure=fam.structure,
        has_siblings=len(fam.siblings) > 0,
        sibling_dynamics=_get_sibling_dynamics(fam.siblings) if fam.siblings else None,
        languages_at_home=fam.languages_at_home,
        family_developmental_history=fam.family_developmental_history,
        support_system=fam.support_system,
    )

    # === 7. CONCERNS ===
    concerns = GestaltConcerns(
        primary_areas=data.primary_concerns or [],
        details=data.concern_details,
        context=data.concern_context,
        urgent_flags=data.urgent_flags or [],
    )

    # === 8. PATTERNS ===
    patterns = GestaltPatterns(
        patterns=[
            {
                "theme": p.theme,
                "observations": p.observations,
                "confidence": p.confidence,
            }
            for p in data.living_edge.patterns
        ]
    )

    # === 9. HYPOTHESES ===
    hypotheses = GestaltHypotheses(
        hypotheses=[
            {
                "theory": h.theory,
                "supporting": h.supporting_evidence,
                "contradicting": h.contradicting_evidence,
                "status": h.status,
            }
            for h in data.living_edge.hypotheses
        ]
    )

    # === 10. OPEN QUESTIONS ===
    open_questions = GestaltOpenQuestions(
        questions=[
            {
                "question": q.question,
                "arose_from": q.arose_from,
                "priority": q.priority,
            }
            for q in data.living_edge.open_questions
        ],
        contradictions=data.living_edge.contradictions,
    )

    # === STORIES ===
    recent_journal = child.get_recent_journal_entries(5)
    recent_stories = [
        {
            "content": entry.content,
            "themes": entry.themes,
            "sentiment": entry.sentiment,
        }
        for entry in recent_journal
    ]
    stories = GestaltStories(
        story_count=len(child.journal_entries),
        recent_stories=recent_stories,
    )

    # === EXPLORATION (unified - conversation/video/mixed) ===
    exploration_activity = data.exploration
    current_cycle = exploration_activity.current_cycle
    current_focus = data.current_focus

    # Build pending questions from conversation method
    pending_questions = []
    if current_cycle and current_cycle.conversation:
        pending_questions = [
            {
                "question": q.question,
                "what_we_hoped_to_learn": q.what_we_hoped_to_learn,
                "target_hypothesis": q.target_hypothesis_id,
            }
            for q in current_cycle.conversation.pending_questions
        ]

    # Build pending video scenarios from video method
    pending_video_scenarios = []
    if current_cycle and current_cycle.video:
        pending_video_scenarios = [
            {
                "scenario": s.scenario,
                "why_we_want_to_see": s.why_we_want_to_see,
                "requested_at": s.requested_at.isoformat() if s.requested_at else None,
            }
            for s in current_cycle.video.pending_scenarios
        ]

    exploration = GestaltExploration(
        has_active_cycle=exploration_activity.has_active_exploration,
        current_cycle_id=current_cycle.id if current_cycle else None,
        current_cycle_started=current_cycle.started_at if current_cycle else None,
        exploration_goal=current_cycle.exploration_goal if current_cycle else None,
        methods_used=current_cycle.methods_used if current_cycle else [],
        hypotheses_being_tested=current_cycle.hypothesis_ids if current_cycle else [],
        questions_being_explored=current_cycle.open_question_ids if current_cycle else [],
        pending_questions=pending_questions,
        pending_video_scenarios=pending_video_scenarios,
        pending_video_analyses=[v.id for v in child.videos if v.analysis_status == "analyzing"],
        new_videos_not_discussed=current_focus.new_videos_not_discussed,
        new_analyses_not_discussed=current_focus.new_analyses_not_discussed,
        completed_cycles_count=len(exploration_activity.get_completed_cycles(100)),
        total_videos_analyzed=child.analyzed_video_count,
    )

    # === SYNTHESES (activity-based) ===
    current_synthesis = exploration_activity.current_synthesis
    days_since = exploration_activity.days_since_last_synthesis()

    syntheses = GestaltSyntheses(
        has_current_synthesis=current_synthesis is not None,
        current_synthesis_id=current_synthesis.id if current_synthesis else None,
        current_synthesis_date=current_synthesis.created_at if current_synthesis else None,
        days_since_last_synthesis=days_since,
        significant_changes_since=current_synthesis.significant_changes_since if current_synthesis else [],
        synthesis_might_be_outdated=(
            current_synthesis is not None and
            (not current_synthesis.is_current or (days_since and days_since > 30))
        ),
        total_syntheses_count=len(exploration_activity.syntheses),
        new_syntheses_not_discussed=current_focus.new_syntheses_not_discussed,
    )

    # === SESSION ===
    session_info = GestaltSession(
        turn_count=session.turn_count,
        message_count=session.message_count,
        is_returning=session.message_count > 0,
        time_since_last=_calculate_time_since_last(current_focus),
        last_session_emotional_state=current_focus.last_session_emotional_tone,
        open_threads=current_focus.open_threads,
        active_card_ids=[card.card_id for card in session.active_cards],
    )

    # === COMPLETENESS ===
    completeness = _calculate_completeness(data, child)

    return Gestalt(
        child_id=child.child_id,
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
        exploration=exploration,
        syntheses=syntheses,
        session=session_info,
        completeness=completeness,
        filming_preference=data.filming_preference,
        parent_goals=data.parent_goals,
        parent_emotional_state=data.parent_emotional_state,
    )


def _calculate_time_since_last(focus: CurrentFocus) -> Optional[timedelta]:
    """Calculate time since last interaction."""
    if focus.last_interaction_at:
        return datetime.now() - focus.last_interaction_at
    return None


def _get_sibling_dynamics(siblings: List) -> Optional[str]:
    """Extract relevant sibling dynamics for prompt."""
    dynamics = []
    for sibling in siblings:
        if sibling.notes:
            dynamics.append(sibling.notes)
    return "; ".join(dynamics) if dynamics else None


def _calculate_completeness(data: DevelopmentalData, child: Child) -> GestaltCompleteness:
    """
    Calculate completeness with expanded tracking.

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
    if not data.child_name:
        missing_essentials.append("name")
    else:
        score += 0.075
    if not data.age:
        missing_essentials.append("age")
    else:
        score += 0.075

    # Strengths (15%)
    missing_strengths = not (
        data.strengths.abilities or
        data.strengths.interests or
        data.strengths.what_lights_them_up
    )
    if not missing_strengths:
        score += 0.15

    # Essence (10%)
    missing_essence = not (
        data.essence.temperament_observations or
        data.essence.core_qualities
    )
    if not missing_essence:
        score += 0.10

    # History (15%)
    missing_history = []
    if not (data.history.birth.complications or data.history.birth.premature is not None):
        missing_history.append("birth")
    else:
        score += 0.05
    if not data.history.milestone_notes:
        missing_history.append("milestones")
    else:
        score += 0.05
    if not data.history.previous_evaluations and not data.history.previous_diagnoses:
        missing_history.append("previous_evaluations")
    else:
        score += 0.05

    # Family (10%)
    missing_family = []
    if not data.family.structure:
        missing_family.append("structure")
    else:
        score += 0.05
    if not data.family.languages_at_home:
        missing_family.append("languages")
    else:
        score += 0.025
    if not data.family.family_developmental_history:
        missing_family.append("family_history")
    else:
        score += 0.025

    # Concerns (15%)
    if data.primary_concerns:
        score += 0.075
    if data.concern_details:
        score += 0.075

    # Observations (10%)
    if len(child.journal_entries) > 0:
        score += 0.05
    if child.video_count > 0:
        score += 0.05

    # Living edge (10%)
    if data.living_edge.patterns:
        score += 0.05
    if data.living_edge.hypotheses or data.living_edge.open_questions:
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

    # Hypotheses
    if gestalt.hypotheses.has_hypotheses:
        known["hypotheses"] = [h["theory"] for h in gestalt.hypotheses.hypotheses]

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
