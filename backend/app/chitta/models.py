"""
Chitta Data Models - Lean and Purposeful

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

These models support the Living Gestalt architecture:
- Simple dataclasses over complex Pydantic models where appropriate
- Clear purpose for each model
- No completeness anywhere
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid


def generate_id() -> str:
    """Generate a short unique ID."""
    return str(uuid.uuid4())[:8]


# === Journal & Stories ===

@dataclass
class JournalEntry:
    """
    Lean journal entry - 4 fields.

    Captures a moment from conversation without overhead.
    """
    timestamp: datetime
    summary: str
    learned: List[str]
    significance: str  # "routine" | "notable" | "breakthrough"

    @classmethod
    def create(
        cls,
        summary: str,
        learned: List[str],
        significance: str = "routine"
    ) -> "JournalEntry":
        """Create a new journal entry with current timestamp."""
        return cls(
            timestamp=datetime.now(),
            summary=summary,
            learned=learned,
            significance=significance,
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


# === Facts & Evidence ===

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
    The Gestalt's understanding of the child.

    This is the accumulated knowledge, not completeness score.
    """
    facts: List[TemporalFact] = field(default_factory=list)
    essence: Optional[Essence] = None
    patterns: List["Pattern"] = field(default_factory=list)

    def add_fact(self, fact: TemporalFact):
        """Add a fact to understanding."""
        self.facts.append(fact)

    def add_pattern(self, pattern: "Pattern"):
        """Add a pattern to understanding."""
        self.patterns.append(pattern)

    def get_facts_by_domain(self, domain: str) -> List[TemporalFact]:
        """Get all facts for a domain."""
        return [f for f in self.facts if f.domain == domain]

    def to_text(self) -> str:
        """Convert understanding to text for prompts."""
        sections = []

        if self.essence and self.essence.narrative:
            sections.append(f"מי הוא: {self.essence.narrative}")

        # Group facts by domain
        domains: Dict[str, List[str]] = {}
        for fact in self.facts:
            domain = fact.domain or "general"
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(fact.content)

        for domain, facts in domains.items():
            sections.append(f"{domain}: {'; '.join(facts[:3])}")

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

    # STATUS
    status: str = "pending"             # pending | uploaded | analyzed | validation_failed
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


# === Exploration Cycles ===

@dataclass
class ExplorationCycle:
    """
    A focused investigation.

    Supports all 4 curiosity types via optional fields.
    Cycles are time-bounded - when complete, they're frozen.

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
    ) -> "ExplorationCycle":
        """Create a hypothesis exploration cycle."""
        return cls(
            id=generate_id(),
            curiosity_type="hypothesis",
            focus=focus,
            focus_domain=domain,
            theory=theory,
            confidence=0.5,
            video_appropriate=video_appropriate,
        )

    @classmethod
    def create_for_question(
        cls,
        focus: str,
        question: str,
        domain: str,
    ) -> "ExplorationCycle":
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
    ) -> "ExplorationCycle":
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
    ) -> "ExplorationCycle":
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
class ExtractionResult:
    """
    Result from Phase 1 (extraction with tools).

    Contains the tool calls made by the LLM when perceiving
    and extracting from the parent's message.
    """
    tool_calls: List[ToolCall]
    perceived_intent: str  # 'story' | 'informational' | 'question' | 'emotional' | 'conversational'


@dataclass
class TurnContext:
    """
    Context for processing a turn.

    Built BEFORE Phase 1 - contains everything the extraction LLM needs.
    NOTE: No intent detection here - that happens INSIDE Phase 1 LLM.
    """
    understanding: Understanding
    curiosities: List[Any]  # List[Curiosity] - using Any to avoid circular import
    recent_history: List[Dict[str, str]]  # List of {role, content} messages
    this_message: str


@dataclass
class Response:
    """Response from the Gestalt."""
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

    # Metadata
    version: int = 1                            # Incremented on each update
    previous_version_summary: Optional[str] = None  # Brief note on what changed

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
            created_at=created_at,
            based_on_observations_through=based_on,
            version=data.get("version", 1),
            previous_version_summary=data.get("previous_version_summary"),
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

def parse_temporal(when: Optional[str]) -> Optional[datetime]:
    """
    Parse a temporal expression to datetime.

    Handles expressions like "yesterday", "usually", "at age 2".
    Returns None if cannot parse or expression is vague.
    """
    if not when:
        return None

    when_lower = when.lower().strip()

    # Current time references
    if when_lower in ["now", "עכשיו", "היום", "today"]:
        return datetime.now()

    # Yesterday
    if when_lower in ["yesterday", "אתמול"]:
        from datetime import timedelta
        return datetime.now() - timedelta(days=1)

    # Vague expressions - return None (still valid, just imprecise)
    vague_terms = ["usually", "generally", "often", "sometimes", "בדרך כלל", "לעיתים"]
    if any(term in when_lower for term in vague_terms):
        return None

    # Age expressions - return None (relative to birth, not absolute)
    if "age" in when_lower or "גיל" in when_lower:
        return None

    # Try ISO format parse
    try:
        return datetime.fromisoformat(when)
    except ValueError:
        pass

    # Default: return None for unparseable expressions
    return None
