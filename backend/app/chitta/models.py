"""
Chitta Data Models - Lean and Purposeful

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

These models support the Darshan architecture:
- Simple dataclasses over complex Pydantic models where appropriate
- Clear purpose for each model
- No completeness anywhere
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import uuid


def generate_id() -> str:
    """Generate a short unique ID."""
    return str(uuid.uuid4())[:8]


# === Parent Context (for gender-appropriate responses) ===

@dataclass
class ParentContext:
    """
    Context about the current parent for gender-appropriate responses.

    Used to inject parent gender into LLM prompts so Chitta uses
    correct Hebrew verb forms (feminine/masculine).
    """
    name: str
    gender: str  # "female" or "male" (derived from role: mother→female, father→male)
    role: str    # "mother" or "father"

    @classmethod
    def from_role(cls, name: str, role: str) -> "ParentContext":
        """Create ParentContext from name and role."""
        gender = "female" if role == "mother" else "male"
        return cls(name=name, gender=gender, role=role)


# === Developmental Timeline (SKELETON - Future Feature) ===

@dataclass
class DevelopmentalMilestone:
    """
    SKELETON - NOT YET IMPLEMENTED

    A significant developmental event in the child's life.

    This is the foundation for a proper developmental timeline feature.
    Unlike system events (when we analyzed a video), these are real-world
    developmental moments that matter to parents and clinicians.

    FUTURE IMPLEMENTATION NOTES:
    - Belongs in the child's Understanding (part of Darshan state)
    - Should be displayed in ChildSpace - either in "מה גילינו" tab
      transformed into a developmental timeline, or as a dedicated view
    - Extraction: LLM tool during conversation when parent mentions milestones
    - Display: Age-based timeline (not date-based) showing child's journey

    Examples:
    - "First words at 12 months"
    - "Started walking at 14 months"
    - "Regression in speech at 2 years"
    - "Started OT therapy at 3 years"
    - "Toilet trained at 3.5 years"

    Required for implementation:
    1. Add `developmental_milestones: List[DevelopmentalMilestone]` to Darshan
    2. Create LLM tool: `record_milestone` for extraction during conversation
    3. Update ChildSpace UI to display age-based timeline
    4. Consider: auto-extraction from existing observations that have temporal info
    """
    id: str
    description: str              # What happened: "אמר מילה ראשונה"
    age_months: Optional[int]     # Age when it happened (in months)
    age_description: Optional[str] # Or free text: "בגיל שנה", "לפני חצי שנה"
    domain: str                   # motor, language, social, emotional, cognitive, behavioral
    milestone_type: str           # achievement, concern, regression, intervention, observation
    source: str                   # conversation, parent_report, clinical
    recorded_at: datetime
    occurred_at: Optional[datetime] = None  # Calculated: when this actually happened
    notes: Optional[str] = None

    @classmethod
    def create(
        cls,
        description: str,
        domain: str,
        milestone_type: str = "observation",
        age_months: Optional[int] = None,
        age_description: Optional[str] = None,
        source: str = "conversation",
        notes: Optional[str] = None,
        child_birth_date: Optional["date"] = None,
    ) -> "DevelopmentalMilestone":
        # Calculate occurred_at from age_months and birth_date
        occurred_at = None
        if age_months is not None and child_birth_date is not None:
            occurred_at = datetime.combine(
                child_birth_date + timedelta(days=age_months * 30),
                datetime.min.time()
            )

        return cls(
            id=generate_id(),
            description=description,
            age_months=age_months,
            age_description=age_description,
            domain=domain,
            milestone_type=milestone_type,
            source=source,
            recorded_at=datetime.now(),
            occurred_at=occurred_at,
            notes=notes,
        )


# === Journal & Stories ===

@dataclass
class JournalEntry:
    """
    Lean journal entry - 5 fields.

    Captures a moment from conversation without overhead.

    Entry types for journey timeline (גילויים):
    - session_started: First interaction began
    - exploration_started: New exploration/curiosity spawned
    - story_captured: Parent shared a meaningful story
    - milestone_recorded: Developmental milestone noted
    - pattern_found: Cross-domain pattern detected
    - insight: General insight/learning
    """
    timestamp: datetime
    summary: str
    learned: List[str]
    significance: str  # "routine" | "notable" | "breakthrough"
    entry_type: str = "insight"  # Type for journey timeline display

    @classmethod
    def create(
        cls,
        summary: str,
        learned: List[str],
        significance: str = "routine",
        entry_type: str = "insight"
    ) -> "JournalEntry":
        """Create a new journal entry with current timestamp."""
        return cls(
            timestamp=datetime.now(),
            summary=summary,
            learned=learned,
            significance=significance,
            entry_type=entry_type,
        )


@dataclass
class Story:
    """
    A captured story from conversation.

    Stories are GOLD - a skilled observer sees MULTIPLE signals in ONE story.
    """
    summary: str
    reveals: List[str]  # What developmental signals this reveals
    domains: List[str]  # Domains touched (social, emotional, motor, etc.)
    significance: float  # 0-1, how significant to understanding
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        summary: str,
        reveals: List[str],
        domains: List[str],
        significance: float = 0.5
    ) -> "Story":
        """Create a new story with current timestamp."""
        return cls(
            summary=summary,
            reveals=reveals,
            domains=domains,
            significance=significance,
        )


# === Observations & Evidence ===

@dataclass
class TemporalFact:
    """
    A fact with temporal validity.

    Facts are observations that are true at a point in time.
    "In November, parent said transitions were hard" is always true.
    """
    content: str
    domain: Optional[str] = None  # Developmental domain
    source: str = "conversation"  # "conversation" | "video" | "parent_update"
    t_valid: Optional[datetime] = None  # When this was true
    t_created: datetime = field(default_factory=datetime.now)
    confidence: float = 0.7

    @classmethod
    def from_observation(
        cls,
        content: str,
        domain: Optional[str] = None,
        confidence: float = 0.7
    ) -> "TemporalFact":
        """Create a fact from a conversation observation."""
        return cls(
            content=content,
            domain=domain,
            source="conversation",
            confidence=confidence,
        )


@dataclass
class Evidence:
    """
    Evidence for an exploration cycle.

    Evidence is immutable and timestamped - a record of what was observed.
    """
    content: str
    effect: str  # "supports" | "contradicts" | "transforms"
    source: str  # "conversation" | "video"
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        content: str,
        effect: str = "supports",
        source: str = "conversation"
    ) -> "Evidence":
        """Create new evidence with current timestamp."""
        return cls(
            content=content,
            effect=effect,
            source=source,
        )


# === Understanding ===

@dataclass
class Essence:
    """Who this child IS as a person."""
    narrative: Optional[str] = None
    temperament: List[str] = field(default_factory=list)
    core_qualities: List[str] = field(default_factory=list)


@dataclass
class Understanding:
    """
    Darshan's understanding of the child.

    This is the accumulated knowledge, not completeness score.
    """
    observations: List[TemporalFact] = field(default_factory=list)
    essence: Optional[Essence] = None
    patterns: List["Pattern"] = field(default_factory=list)
    milestones: List["DevelopmentalMilestone"] = field(default_factory=list)

    def add_observation(self, observation: TemporalFact):
        """Add an observation to understanding."""
        self.observations.append(observation)

    def add_pattern(self, pattern: "Pattern"):
        """Add a pattern to understanding."""
        self.patterns.append(pattern)

    def add_milestone(self, milestone: "DevelopmentalMilestone"):
        """Add a developmental milestone."""
        self.milestones.append(milestone)

    def get_observations_by_domain(self, domain: str) -> List[TemporalFact]:
        """Get all observations for a domain."""
        return [o for o in self.observations if o.domain == domain]

    def to_text(self) -> str:
        """Convert understanding to text for prompts."""
        sections = []

        if self.essence and self.essence.narrative:
            sections.append(f"מי הוא: {self.essence.narrative}")

        # Group observations by domain
        domains: Dict[str, List[str]] = {}
        for obs in self.observations:
            domain = obs.domain or "general"
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(obs.content)

        for domain, obs_list in domains.items():
            sections.append(f"{domain}: {'; '.join(obs_list[:3])}")

        if self.patterns:
            patterns_text = ", ".join(p.description for p in self.patterns[:3])
            sections.append(f"דפוסים: {patterns_text}")

        return "\n".join(sections) if sections else "עדיין מתחילים להכיר."


@dataclass
class Pattern:
    """A cross-domain pattern detected in the child."""
    description: str
    domains_involved: List[str]
    confidence: float = 0.5
    detected_at: datetime = field(default_factory=datetime.now)
    # Optional title for parent-friendly display (generated by LLM)
    title: Optional[str] = None


@dataclass
class PortraitSection:
    """
    A thematic section in the child's portrait.

    These are parent-friendly, digestible insights about the child,
    organized by theme rather than by data type.

    Example sections:
    - "העולם הפנימי והיצירה" - The inner world and creativity
    - "התמודדות עם שינויים" - Dealing with changes
    - "הסביבה האופטימלית עבורו" - The optimal environment for them

    Each section has:
    - A meaningful title (not "מה שמנו לב" generic)
    - An icon (emoji)
    - Content (paragraph or bullet points)
    """
    title: str              # Meaningful thematic title in Hebrew
    icon: str               # Emoji icon (🧩, ⏳, 🌱, etc.)
    content: str            # The insight content - paragraph or bullets
    content_type: str = "paragraph"  # "paragraph" | "bullets"


# === Baseline Video Request ===

@dataclass
class BaselineVideoRequest:
    """
    Early-relationship request for a baseline video.

    Not tied to any hypothesis - captures unknown unknowns.
    Suggested after initial rapport, before strong theories form.

    This is for DISCOVERY video value - seeing the child before
    we know what to look for.
    """
    id: str
    status: str = "pending"  # pending | accepted | declined | uploaded | analyzed

    # Timing
    suggested_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None

    # Parent-facing (simple, warm)
    parent_instruction: str = "צלמי 3-5 דקות של משחק חופשי רגיל ביחד"
    why_helpful: str = "זה עוזר לנו להכיר אותו בדרך שמשלימה את מה שאת מספרת"

    # Video
    video_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    # Analysis results
    analysis_result: Optional[Dict[str, Any]] = None
    analyzed_at: Optional[datetime] = None
    discoveries: List[str] = field(default_factory=list)  # What we learned

    @classmethod
    def create(cls) -> "BaselineVideoRequest":
        """Create a new baseline video request."""
        return cls(
            id=generate_id(),
            suggested_at=datetime.now(),
        )

    def accept(self):
        """Parent accepted the suggestion."""
        self.status = "accepted"
        self.accepted_at = datetime.now()

    def decline(self):
        """Parent declined - respect it."""
        self.status = "declined"

    def mark_uploaded(self, video_path: str):
        """Mark video as uploaded."""
        self.status = "uploaded"
        self.video_path = video_path
        self.uploaded_at = datetime.now()

    def mark_analyzed(self, analysis_result: Dict[str, Any], discoveries: List[str]):
        """Mark video as analyzed with discoveries."""
        self.status = "analyzed"
        self.analysis_result = analysis_result
        self.analyzed_at = datetime.now()
        self.discoveries = discoveries

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for persistence."""
        return {
            "id": self.id,
            "status": self.status,
            "suggested_at": self.suggested_at.isoformat() if self.suggested_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "parent_instruction": self.parent_instruction,
            "why_helpful": self.why_helpful,
            "video_path": self.video_path,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "analysis_result": self.analysis_result,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "discoveries": self.discoveries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaselineVideoRequest":
        """Create from dict (persistence loading)."""
        suggested_at = None
        if data.get("suggested_at"):
            try:
                suggested_at = datetime.fromisoformat(data["suggested_at"])
            except (ValueError, TypeError):
                pass

        accepted_at = None
        if data.get("accepted_at"):
            try:
                accepted_at = datetime.fromisoformat(data["accepted_at"])
            except (ValueError, TypeError):
                pass

        uploaded_at = None
        if data.get("uploaded_at"):
            try:
                uploaded_at = datetime.fromisoformat(data["uploaded_at"])
            except (ValueError, TypeError):
                pass

        analyzed_at = None
        if data.get("analyzed_at"):
            try:
                analyzed_at = datetime.fromisoformat(data["analyzed_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get("id", generate_id()),
            status=data.get("status", "pending"),
            suggested_at=suggested_at,
            accepted_at=accepted_at,
            parent_instruction=data.get("parent_instruction", "צלמי 3-5 דקות של משחק חופשי רגיל ביחד"),
            why_helpful=data.get("why_helpful", "זה עוזר לנו להכיר אותו בדרך שמשלימה את מה שאת מספרת"),
            video_path=data.get("video_path"),
            uploaded_at=uploaded_at,
            analysis_result=data.get("analysis_result"),
            analyzed_at=analyzed_at,
            discoveries=data.get("discoveries", []),
        )


# === Video Scenarios ===

@dataclass
class VideoScenario:
    """
    A video filming scenario for testing a hypothesis.

    PARENT-FACING fields are warm and concrete (no hypothesis revealed).
    INTERNAL fields are for analysis (not shown to parent).

    Guidelines are generated ONLY after parent consent.
    """
    id: str

    # PARENT-FACING (warm, concrete, no hypothesis revealed)
    title: str                          # "משחק קופסה במטבח"
    what_to_film: str                   # Concrete filming instructions
    rationale_for_parent: str           # Sandwich: validate→explain→reassure
    duration_suggestion: str            # "5-7 דקות"
    example_situations: List[str] = field(default_factory=list)  # Specific to their context

    # INTERNAL (for analysis, NOT shown to parent)
    target_hypothesis_id: str = ""      # Links to exploration cycle
    what_we_hope_to_learn: str = ""     # Clinical goal
    focus_points: List[str] = field(default_factory=list)  # What analyst looks for
    category: str = "hypothesis_test"   # hypothesis_test | pattern_exploration | strength_baseline

    # STATUS & TIMESTAMPS
    status: str = "pending"             # pending | uploaded | needs_confirmation | analyzed | acknowledged | validation_failed | rejected
    created_at: Optional[datetime] = None  # When guidelines were generated
    reminder_dismissed: bool = False    # True = don't show reminder card, but guidelines still accessible
    video_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    analysis_result: Optional[Dict[str, Any]] = None
    analyzed_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        title: str,
        what_to_film: str,
        rationale_for_parent: str,
        target_hypothesis_id: str,
        what_we_hope_to_learn: str,
        focus_points: List[str],
        duration_suggestion: str = "5-7 דקות",
        example_situations: List[str] = None,
        category: str = "hypothesis_test",
    ) -> "VideoScenario":
        """Create a new video scenario."""
        return cls(
            id=generate_id(),
            title=title,
            what_to_film=what_to_film,
            rationale_for_parent=rationale_for_parent,
            duration_suggestion=duration_suggestion,
            example_situations=example_situations or [],
            target_hypothesis_id=target_hypothesis_id,
            what_we_hope_to_learn=what_we_hope_to_learn,
            focus_points=focus_points,
            category=category,
            created_at=datetime.now(),  # Track when guidelines were generated
        )

    def mark_uploaded(self, video_path: str):
        """Mark scenario as uploaded."""
        self.status = "uploaded"
        self.video_path = video_path
        self.uploaded_at = datetime.now()

    def mark_analyzed(self, analysis_result: Dict[str, Any]):
        """Mark scenario as analyzed."""
        self.status = "analyzed"
        self.analysis_result = analysis_result
        self.analyzed_at = datetime.now()

    def mark_validation_failed(self, analysis_result: Dict[str, Any]):
        """Mark scenario as validation failed - allows retry with new video."""
        self.status = "validation_failed"
        self.analysis_result = analysis_result
        self.analyzed_at = datetime.now()
        # Keep video_path so we know what was uploaded (for debugging)
        # Parent can upload a new video to replace it

    def dismiss_reminder(self):
        """
        Dismiss the reminder card but keep guidelines accessible.

        Parent doesn't want to be reminded, but might still want to film later.
        Guidelines stay in ChildSpace Observations tab.
        """
        self.reminder_dismissed = True

    def reject(self):
        """
        Reject these guidelines - parent decided not to film this scenario.

        This closes the scenario permanently. The hypothesis might still
        be valid, but this particular filming request is declined.
        """
        self.status = "rejected"

    def to_parent_facing_dict(self) -> Dict[str, Any]:
        """Return only parent-facing fields (no hypothesis details)."""
        return {
            "id": self.id,
            "title": self.title,
            "what_to_film": self.what_to_film,
            "why_matters": self.rationale_for_parent,  # Frontend expects 'why_matters'
            "duration": self.duration_suggestion,
            "example_situations": self.example_situations,
            "status": self.status,
        }


# === Explorations ===

@dataclass
class Exploration:
    """
    A focused investigation — following a thread of curiosity.

    Supports all 4 curiosity types via optional fields.
    Explorations are time-bounded - when complete, they're frozen.

    Video exploration requires EXPLICIT CONSENT before guidelines are generated.
    """
    id: str
    curiosity_type: str  # "discovery" | "question" | "hypothesis" | "pattern"
    focus: str
    focus_domain: str
    status: str = "active"  # "active" | "complete" | "stale"
    created_at: datetime = field(default_factory=datetime.now)

    # Evidence (all types)
    evidence: List[Evidence] = field(default_factory=list)

    # Type-specific fields
    theory: Optional[str] = None           # hypothesis
    confidence: Optional[float] = None     # hypothesis
    video_appropriate: bool = False        # hypothesis - LLM determines if observable
    question: Optional[str] = None         # question
    answer_fragments: List[str] = field(default_factory=list)  # question
    discovery_aspect: Optional[str] = None # discovery (essence/strengths/context)
    pattern_observation: Optional[str] = None  # pattern
    supporting_cycle_ids: List[str] = field(default_factory=list)  # pattern

    # Video value (LLM-determined) - WHY video would be valuable
    video_value: Optional[str] = None      # calibration | chain | discovery | reframe | relational
    video_value_reason: Optional[str] = None  # Brief explanation of what video could reveal

    # Video consent and scenarios (guidelines generated ONLY after consent)
    video_accepted: bool = False           # Parent said YES to video
    video_declined: bool = False           # Parent said NO - respect it, don't re-ask
    video_suggested_at: Optional[datetime] = None  # When we suggested video
    video_scenarios: List[VideoScenario] = field(default_factory=list)  # Generated after consent
    guidelines_status: Optional[str] = None  # "generating" | "ready" | "error"

    def add_evidence(self, evidence: Evidence):
        """Add evidence and update confidence if hypothesis."""
        self.evidence.append(evidence)

        if self.curiosity_type == "hypothesis" and self.confidence is not None:
            if evidence.effect == "supports":
                self.confidence = min(1.0, self.confidence + 0.1)
            elif evidence.effect == "contradicts":
                self.confidence = max(0.0, self.confidence - 0.15)

    def complete(self):
        """Mark cycle as complete."""
        self.status = "complete"

    def mark_stale(self):
        """Mark cycle as stale (inactive for too long)."""
        self.status = "stale"

    # Video consent methods
    def accept_video(self):
        """Parent accepted video suggestion."""
        self.video_accepted = True
        self.video_declined = False

    def decline_video(self):
        """Parent declined video - respect it, don't re-ask for this cycle."""
        self.video_declined = True
        self.video_accepted = False

    def mark_video_suggested(self):
        """Mark when we suggested video to parent."""
        self.video_suggested_at = datetime.now()

    def can_suggest_video(self) -> bool:
        """Check if we can suggest video for this cycle."""
        return (
            self.video_appropriate and
            not self.video_accepted and
            not self.video_declined and
            not self.video_scenarios  # No guidelines generated yet
        )

    def has_pending_videos(self) -> bool:
        """Check if there are uploaded videos waiting for analysis."""
        return any(s.status == "uploaded" for s in self.video_scenarios)

    def has_analyzed_videos(self) -> bool:
        """Check if any videos have been analyzed."""
        return any(s.status == "analyzed" for s in self.video_scenarios)

    def get_scenario(self, scenario_id: str) -> Optional[VideoScenario]:
        """Get a video scenario by ID."""
        for scenario in self.video_scenarios:
            if scenario.id == scenario_id:
                return scenario
        return None

    @classmethod
    def create_for_hypothesis(
        cls,
        focus: str,
        theory: str,
        domain: str,
        video_appropriate: bool = True,
        video_value: Optional[str] = None,
        video_value_reason: Optional[str] = None,
    ) -> "Exploration":
        """Create a hypothesis exploration cycle."""
        return cls(
            id=generate_id(),
            curiosity_type="hypothesis",
            focus=focus,
            focus_domain=domain,
            theory=theory,
            confidence=0.5,
            video_appropriate=video_appropriate,
            video_value=video_value,
            video_value_reason=video_value_reason,
        )

    @classmethod
    def create_for_question(
        cls,
        focus: str,
        question: str,
        domain: str,
    ) -> "Exploration":
        """Create a question exploration cycle."""
        return cls(
            id=generate_id(),
            curiosity_type="question",
            focus=focus,
            focus_domain=domain,
            question=question,
        )

    @classmethod
    def create_for_discovery(
        cls,
        focus: str,
        aspect: str,
        domain: str,
    ) -> "Exploration":
        """Create a discovery exploration cycle."""
        return cls(
            id=generate_id(),
            curiosity_type="discovery",
            focus=focus,
            focus_domain=domain,
            discovery_aspect=aspect,
        )

    @classmethod
    def create_for_pattern(
        cls,
        focus: str,
        observation: str,
        domains: List[str],
    ) -> "Exploration":
        """Create a pattern exploration cycle."""
        return cls(
            id=generate_id(),
            curiosity_type="pattern",
            focus=focus,
            focus_domain=domains[0] if domains else "general",
            pattern_observation=observation,
        )


# === LLM Interaction Models ===

@dataclass
class ToolCall:
    """A tool call from LLM."""
    name: str
    args: Dict[str, Any]


@dataclass
class PerceptionResult:
    """
    Result from Phase 1 (perception with tools).

    Contains the tool calls made by the LLM when perceiving
    what the parent shared.
    """
    tool_calls: List[ToolCall]
    perceived_intent: str  # 'story' | 'informational' | 'question' | 'emotional' | 'conversational'


@dataclass
class TurnContext:
    """
    Context for processing a turn.

    Built BEFORE Phase 1 - contains everything the perception LLM needs.
    NOTE: No intent detection here - that happens INSIDE Phase 1 LLM.
    """
    understanding: Understanding
    curiosities: List[Any]  # List[Curiosity] - using Any to avoid circular import
    recent_history: List[Dict[str, str]]  # List of {role, content} messages
    this_message: str


@dataclass
class Response:
    """Response from Darshan."""
    text: str
    curiosities: List[Any]  # List[Curiosity]
    open_questions: List[str]
    # Signals that important learning occurred - triggers background crystallization
    should_crystallize: bool = False


# === Memory & Synthesis ===

@dataclass
class ConversationMemory:
    """
    Distilled memory from a session.

    Created on session transition (>4 hour gap).
    """
    summary: str
    distilled_at: datetime
    turn_count: int

    @classmethod
    def create(cls, summary: str, turn_count: int) -> "ConversationMemory":
        """Create a new conversation memory."""
        return cls(
            summary=summary,
            distilled_at=datetime.now(),
            turn_count=turn_count,
        )


@dataclass
class SynthesisReport:
    """
    Synthesis report from deep analysis.

    Created by STRONGEST model on demand.
    """
    essence_narrative: Optional[str]
    patterns: List[Pattern]
    confidence_by_domain: Dict[str, float]
    open_questions: List[str]
    created_at: datetime = field(default_factory=datetime.now)


# === Crystal (Cached Synthesis) ===

@dataclass
class InterventionPathway:
    """A pathway connecting strength/interest to concern."""
    hook: str              # The strength or interest that can help
    concern: str           # The concern it can address
    suggestion: str        # Concrete guidance
    confidence: float = 0.5


@dataclass
class ProfessionalSummary:
    """
    Holistic-first summary for a professional.

    Every recipient gets the WHOLE child - that's Chitta's core value.
    The lens (emphasis) changes based on recipient_type.

    Three threads are always present:
    1. What parents shared - their words, observations, concerns
    2. What we noticed - patterns, connections, behaviors in situations
    3. What remains open - questions worth exploring
    """
    # Core holistic content (same for all recipients)
    who_this_child_is: str           # 2-3 sentences about the whole person
    strengths_and_interests: str     # What opens them up, what they love
    what_parents_shared: str         # Thread 1: Parent observations in their words
    what_we_noticed: str             # Thread 2: Patterns, connections (framed by recipient)
    what_remains_open: str           # Thread 3: Questions worth exploring

    # Recipient-specific lens
    recipient_type: str              # "teacher" | "specialist" | "medical"
    role_specific_section: str       # Different per recipient type:
                                     # - teacher: practical strategies, daily functioning tips
                                     # - specialist: investigation questions, assessment guidance
                                     # - medical: observable patterns, developmental markers

    # The invitation - different framing per recipient
    invitation: str                  # What we hope they'll help explore


@dataclass
class ExpertRecommendation:
    """
    A specific, nuanced recommendation for professional help.

    The magic is in the NON-OBVIOUS match:
    - Not "OT" but "OT with dance/movement background"
    - Not "psychologist" but "psychologist who works with gifted kids"

    The recommendation comes from crossing:
    - What we know works (intervention pathways, interests)
    - Who the child is (temperament, how they connect)
    - What they need (the actual concern)
    """
    # The professional
    profession: str                  # "מטפלת בעיסוק", "פסיכולוג"
    specialization: str              # The NON-OBVIOUS specific match

    # The reasoning (in parent-friendly language)
    why_this_match: str              # Why THIS specific type for THIS child

    # What approach would work
    recommended_approach: str        # "גישה משחקית", "עבודה דרך הגוף"
    why_this_approach: str           # Based on how the child connects

    # Practical guidance for the parent
    what_to_look_for: List[str]      # What to ask/look for when choosing

    # Holistic summaries for different recipients
    professional_summaries: List[ProfessionalSummary] = field(default_factory=list)

    # Confidence and priority
    confidence: float = 0.5          # How confident we are this is needed
    priority: str = "when_ready"     # "when_ready" | "soon" | "important"

    def get_summary_for_recipient(self, recipient_type: str) -> Optional[ProfessionalSummary]:
        """Get the summary tailored for a specific recipient type."""
        for summary in self.professional_summaries:
            if summary.recipient_type == recipient_type:
                return summary
        return None


@dataclass
class Crystal:
    """
    Crystallized understanding - cached synthesis with timestamp tracking.

    The Crystal represents our deep understanding of the child at a point in time.
    It's expensive to create (strongest model) but cached and reused.

    STALENESS DETECTION:
    - based_on_observations_through: timestamp of newest observation when crystal was formed
    - To check staleness: compare with max(fact.t_created, story.timestamp, evidence.timestamp)
    - If newest observation > based_on_observations_through → crystal is stale

    INCREMENTAL UPDATE:
    - When stale, don't regenerate from scratch
    - Send previous crystal + new observations → get updated crystal
    """
    # The synthesis content
    essence_narrative: Optional[str]            # Who this child IS as a whole person
    temperament: List[str]                      # Core temperament traits
    core_qualities: List[str]                   # What makes them them
    patterns: List[Pattern]                     # Cross-domain connections
    intervention_pathways: List[InterventionPathway]  # How strengths help concerns
    open_questions: List[str]                   # What we still wonder

    # Timestamp tracking for staleness
    created_at: datetime                        # When this crystal was formed
    based_on_observations_through: datetime     # Newest observation timestamp at formation

    # Metadata and optional fields (must have defaults, so after required fields)
    version: int = 1                            # Incremented on each update
    previous_version_summary: Optional[str] = None  # Brief note on what changed
    expert_recommendations: List[ExpertRecommendation] = field(default_factory=list)  # Non-obvious professional matches
    portrait_sections: List[PortraitSection] = field(default_factory=list)  # Parent-friendly thematic cards

    @classmethod
    def create_empty(cls) -> "Crystal":
        """Create an empty crystal for new children."""
        now = datetime.now()
        return cls(
            essence_narrative=None,
            temperament=[],
            core_qualities=[],
            patterns=[],
            intervention_pathways=[],
            open_questions=[],
            created_at=now,
            based_on_observations_through=now,
            version=0,
        )

    def is_stale(self, latest_observation_at: datetime) -> bool:
        """Check if crystal is stale relative to newest observation."""
        return latest_observation_at > self.based_on_observations_through

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for persistence."""
        return {
            "essence_narrative": self.essence_narrative,
            "temperament": self.temperament,
            "core_qualities": self.core_qualities,
            "patterns": [
                {
                    "description": p.description,
                    "domains_involved": p.domains_involved,
                    "confidence": p.confidence,
                    "detected_at": p.detected_at.isoformat() if hasattr(p, 'detected_at') else None,
                }
                for p in self.patterns
            ],
            "intervention_pathways": [
                {
                    "hook": ip.hook,
                    "concern": ip.concern,
                    "suggestion": ip.suggestion,
                    "confidence": ip.confidence,
                }
                for ip in self.intervention_pathways
            ],
            "open_questions": self.open_questions,
            "expert_recommendations": [
                {
                    "profession": er.profession,
                    "specialization": er.specialization,
                    "why_this_match": er.why_this_match,
                    "recommended_approach": er.recommended_approach,
                    "why_this_approach": er.why_this_approach,
                    "what_to_look_for": er.what_to_look_for,
                    "professional_summaries": [
                        {
                            "who_this_child_is": ps.who_this_child_is,
                            "strengths_and_interests": ps.strengths_and_interests,
                            "what_parents_shared": ps.what_parents_shared,
                            "what_we_noticed": ps.what_we_noticed,
                            "what_remains_open": ps.what_remains_open,
                            "recipient_type": ps.recipient_type,
                            "role_specific_section": ps.role_specific_section,
                            "invitation": ps.invitation,
                        }
                        for ps in er.professional_summaries
                    ],
                    "confidence": er.confidence,
                    "priority": er.priority,
                }
                for er in self.expert_recommendations
            ],
            "portrait_sections": [
                {
                    "title": ps.title,
                    "icon": ps.icon,
                    "content": ps.content,
                    "content_type": ps.content_type,
                }
                for ps in self.portrait_sections
            ],
            "created_at": self.created_at.isoformat(),
            "based_on_observations_through": self.based_on_observations_through.isoformat(),
            "version": self.version,
            "previous_version_summary": self.previous_version_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Crystal":
        """Create from dict (persistence loading)."""
        patterns = []
        for p_data in data.get("patterns", []):
            detected_at = datetime.now()
            if p_data.get("detected_at"):
                try:
                    detected_at = datetime.fromisoformat(p_data["detected_at"])
                except (ValueError, TypeError):
                    pass
            patterns.append(Pattern(
                description=p_data["description"],
                domains_involved=p_data.get("domains_involved", []),
                confidence=p_data.get("confidence", 0.5),
                detected_at=detected_at,
            ))

        intervention_pathways = []
        for ip_data in data.get("intervention_pathways", []):
            intervention_pathways.append(InterventionPathway(
                hook=ip_data["hook"],
                concern=ip_data["concern"],
                suggestion=ip_data["suggestion"],
                confidence=ip_data.get("confidence", 0.5),
            ))

        expert_recommendations = []
        for er_data in data.get("expert_recommendations", []):
            # Parse professional summaries (new holistic-first format)
            professional_summaries = []
            for ps_data in er_data.get("professional_summaries", []):
                professional_summaries.append(ProfessionalSummary(
                    who_this_child_is=ps_data.get("who_this_child_is", ""),
                    strengths_and_interests=ps_data.get("strengths_and_interests", ""),
                    what_parents_shared=ps_data.get("what_parents_shared", ""),
                    what_we_noticed=ps_data.get("what_we_noticed", ""),
                    what_remains_open=ps_data.get("what_remains_open", ""),
                    recipient_type=ps_data.get("recipient_type", "specialist"),
                    role_specific_section=ps_data.get("role_specific_section", ""),
                    invitation=ps_data.get("invitation", ""),
                ))

            expert_recommendations.append(ExpertRecommendation(
                profession=er_data["profession"],
                specialization=er_data["specialization"],
                why_this_match=er_data["why_this_match"],
                recommended_approach=er_data["recommended_approach"],
                why_this_approach=er_data["why_this_approach"],
                what_to_look_for=er_data.get("what_to_look_for", []),
                professional_summaries=professional_summaries,
                confidence=er_data.get("confidence", 0.5),
                priority=er_data.get("priority", "when_ready"),
            ))

        portrait_sections = []
        for ps_data in data.get("portrait_sections", []):
            portrait_sections.append(PortraitSection(
                title=ps_data["title"],
                icon=ps_data["icon"],
                content=ps_data["content"],
                content_type=ps_data.get("content_type", "paragraph"),
            ))

        created_at = datetime.now()
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass

        based_on = created_at
        if data.get("based_on_observations_through"):
            try:
                based_on = datetime.fromisoformat(data["based_on_observations_through"])
            except (ValueError, TypeError):
                pass

        return cls(
            essence_narrative=data.get("essence_narrative"),
            temperament=data.get("temperament", []),
            core_qualities=data.get("core_qualities", []),
            patterns=patterns,
            intervention_pathways=intervention_pathways,
            open_questions=data.get("open_questions", []),
            expert_recommendations=expert_recommendations,
            portrait_sections=portrait_sections,
            created_at=created_at,
            based_on_observations_through=based_on,
            version=data.get("version", 1),
            previous_version_summary=data.get("previous_version_summary"),
        )


# === Shared Summaries ===

@dataclass
class SharedSummary:
    """
    A summary generated for sharing with a professional or person.

    Persisted to allow accessing previous summaries in later sessions.
    The content includes a timestamp in Hebrew for context.
    """
    id: str
    recipient_type: str           # "professional" | "family" | "custom"
    recipient_description: str    # "מטפלת בעיסוק", "סבתא", etc.
    content: str                  # The actual summary text
    created_at: datetime
    comprehensive: bool = False   # Was this a comprehensive summary?

    # Optional - links to crystal recommendation if relevant
    expert_recommendation_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        recipient_description: str,
        content: str,
        recipient_type: str = "professional",
        comprehensive: bool = False,
        expert_recommendation_id: Optional[str] = None,
    ) -> "SharedSummary":
        """Create a new shared summary with timestamp."""
        return cls(
            id=generate_id(),
            recipient_type=recipient_type,
            recipient_description=recipient_description,
            content=content,
            created_at=datetime.now(),
            comprehensive=comprehensive,
            expert_recommendation_id=expert_recommendation_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for persistence."""
        return {
            "id": self.id,
            "recipient_type": self.recipient_type,
            "recipient_description": self.recipient_description,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "comprehensive": self.comprehensive,
            "expert_recommendation_id": self.expert_recommendation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SharedSummary":
        """Create from dict (persistence loading)."""
        created_at = datetime.now()
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get("id", generate_id()),
            recipient_type=data.get("recipient_type", "professional"),
            recipient_description=data.get("recipient_description", ""),
            content=data.get("content", ""),
            created_at=created_at,
            comprehensive=data.get("comprehensive", False),
            expert_recommendation_id=data.get("expert_recommendation_id"),
        )


# === Message Types ===

@dataclass
class Message:
    """A conversation message."""
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dict for LLM API."""
        return {"role": self.role, "content": self.content}


# === Temporal Parsing ===

def parse_temporal(
    when_type: Optional[str],
    when_value: Optional[float] = None,
    reference_time: Optional[datetime] = None,
    child_birth_date: Optional["date"] = None,
) -> Optional[datetime]:
    """
    Convert structured temporal data (from LLM extraction) to absolute datetime.

    The LLM extracts temporal info into:
    - when_type: enum like "now", "days_ago", "age_months", etc.
    - when_value: numeric value (days, weeks, months, or age in months)

    Args:
        when_type: Type of temporal reference (from enum)
        when_value: Numeric value for the type
        reference_time: When this was recorded (defaults to now)
        child_birth_date: Child's birth date for age-based calculations

    Returns:
        Absolute datetime
    """
    from datetime import timedelta, date

    ref = reference_time or datetime.now()

    if not when_type:
        return ref  # No temporal info - use recording time

    when_type = when_type.lower()
    value = int(when_value) if when_value else 0

    if when_type == "now":
        return ref

    elif when_type == "days_ago":
        return ref - timedelta(days=value)

    elif when_type == "weeks_ago":
        return ref - timedelta(weeks=value)

    elif when_type == "months_ago":
        return ref - timedelta(days=value * 30)

    elif when_type == "age_months":
        # Convert age in months to absolute date using child's birth date
        if child_birth_date:
            return datetime.combine(
                child_birth_date + timedelta(days=value * 30),
                datetime.min.time()
            )
        else:
            return ref  # No birth date available

    elif when_type == "habitual":
        return ref  # Ongoing pattern - use reference time

    elif when_type == "past_unspecified":
        return ref - timedelta(days=30)  # Rough estimate

    else:
        return ref
