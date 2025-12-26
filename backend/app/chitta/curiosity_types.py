"""
Curiosity Types - The Two Natures Architecture

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module implements the curiosity type hierarchy based on CURIOSITY_ARCHITECTURE.md:

TWO NATURES:
- Receptive (Discovery, Question): Open, gathering - measured by FULLNESS
- Assertive (Hypothesis, Pattern): Claiming, testing - measured by CONFIDENCE

TYPE INDEPENDENCE:
- Type = what kind of exploration activity
- Fullness/Confidence = how complete/certain within that type

You can have a sparse discovery (fullness=0.2) or a rich one (fullness=0.8).
You can have a weak hypothesis (confidence=0.3) or a confirmed one (confidence=0.9).

EVOLUTION PATH:
  DISCOVERY → spawns → QUESTION → evolves → HYPOTHESIS → contributes → PATTERN
       ↓                   ↓                    ↓                  ↓
    (fullness)         (fullness)          (confidence)      (confidence)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .models import InvestigationContext


def generate_curiosity_id(prefix: str = "cur") -> str:
    """Generate a unique curiosity ID."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# =============================================================================
# Status Enums (as string literals with validation)
# =============================================================================

DISCOVERY_STATUSES = {"sparse", "growing", "rich", "dormant"}
QUESTION_STATUSES = {"open", "partial", "answered", "evolved", "dormant"}
HYPOTHESIS_STATUSES = {"weak", "testing", "supported", "confirmed", "refuted", "transformed", "dormant"}
PATTERN_STATUSES = {"emerging", "solid", "foundational", "questioned", "dissolved"}


# =============================================================================
# Base Classes
# =============================================================================

@dataclass
class BaseCuriosity(ABC):
    """
    Abstract base class for all curiosity types.

    All curiosities share:
    - Identity: id, focus, domain
    - Urgency: pull (decays over time, system applies)
    - Status: type-specific lifecycle state
    - Temporal: created_at, last_updated
    - Provenance: REQUIRED reasoning for explainability
    """
    id: str
    focus: str  # What we're curious about (Hebrew, concise)
    domain: str  # Primary developmental domain

    pull: float  # 0-1, how urgently to explore (LLM sets, system decays)
    status: str  # Type-specific status

    # Temporal
    created_at: datetime
    last_updated: datetime

    # REQUIRED Provenance - for explainability and audit
    created_reasoning: str  # Why was this curiosity created?
    last_updated_reasoning: str  # Why the last change?

    @property
    @abstractmethod
    def curiosity_type(self) -> str:
        """Return the type name: discovery, question, hypothesis, pattern."""
        pass

    @property
    @abstractmethod
    def nature(self) -> str:
        """Return the nature: receptive or assertive."""
        pass

    @property
    @abstractmethod
    def metric_value(self) -> float:
        """Return fullness for receptive, confidence for assertive."""
        pass

    @property
    @abstractmethod
    def metric_name(self) -> str:
        """Return the metric name: fullness or confidence."""
        pass

    def touch(self, reasoning: str):
        """Update last_updated timestamp and reasoning."""
        self.last_updated = datetime.now()
        self.last_updated_reasoning = reasoning

    def is_active(self) -> bool:
        """Check if curiosity is in an active (non-dormant) state."""
        return self.status != "dormant"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for persistence."""
        return {
            "id": self.id,
            "type": self.curiosity_type,
            "nature": self.nature,
            "focus": self.focus,
            "domain": self.domain,
            "pull": self.pull,
            "status": self.status,
            self.metric_name: self.metric_value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "created_reasoning": self.created_reasoning,
            "last_updated_reasoning": self.last_updated_reasoning,
        }

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseCuriosity":
        """Deserialize from dict."""
        pass


@dataclass
class ReceptiveCuriosity(BaseCuriosity):
    """
    Base class for receptive curiosities (Discovery, Question).

    Receptive = Open, receiving, gathering
    Measured by FULLNESS: How complete is our picture?

    Fullness increases as observations accumulate.
    Fullness does NOT decay (understanding persists).
    """
    fullness: float = 0.1  # 0-1, how complete is our picture

    @property
    def nature(self) -> str:
        return "receptive"

    @property
    def metric_value(self) -> float:
        return self.fullness

    @property
    def metric_name(self) -> str:
        return "fullness"

    def update_fullness(self, new_fullness: float, reasoning: str):
        """Update fullness with required reasoning."""
        self.fullness = max(0.0, min(1.0, new_fullness))
        self.touch(reasoning)


@dataclass
class AssertiveCuriosity(BaseCuriosity):
    """
    Base class for assertive curiosities (Hypothesis, Pattern).

    Assertive = Claiming, testing, proving
    Measured by CONFIDENCE: How sure are we this is true?

    Confidence changes with evidence.
    Confidence does NOT decay (certainty persists unless contradicted).
    """
    confidence: float = 0.3  # 0-1, how sure are we this is true

    @property
    def nature(self) -> str:
        return "assertive"

    @property
    def metric_value(self) -> float:
        return self.confidence

    @property
    def metric_name(self) -> str:
        return "confidence"

    def update_confidence(self, new_confidence: float, reasoning: str):
        """Update confidence with required reasoning."""
        self.confidence = max(0.0, min(1.0, new_confidence))
        self.touch(reasoning)


# =============================================================================
# Concrete Types
# =============================================================================

@dataclass
class Discovery(ReceptiveCuriosity):
    """
    Open exploration of a domain.

    Discovery is the soil from which other curiosities grow.
    It's about open receiving - "What is there to see?"

    Examples:
    - "עולם המשחק שלו" (His play world)
    - "מי הילד הזה?" (Who is this child?)
    - "מה הוא אוהב?" (What does he love?)

    Status progression: sparse → growing → rich
    Can become dormant if not touched for a long time.
    """
    # Lineage: what grew from this discovery
    spawned_curiosities: List[str] = field(default_factory=list)  # IDs of questions/hypotheses

    @property
    def curiosity_type(self) -> str:
        return "discovery"

    def spawn_curiosity(self, curiosity_id: str, reasoning: str):
        """Record that a new curiosity spawned from this discovery."""
        if curiosity_id not in self.spawned_curiosities:
            self.spawned_curiosities.append(curiosity_id)
        self.touch(reasoning)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["spawned_curiosities"] = self.spawned_curiosities
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Discovery":
        return cls(
            id=data["id"],
            focus=data["focus"],
            domain=data["domain"],
            pull=data.get("pull", 0.5),
            status=data.get("status", "sparse"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            last_updated=datetime.fromisoformat(data["last_updated"]) if isinstance(data.get("last_updated"), str) else data.get("last_updated", datetime.now()),
            created_reasoning=data.get("created_reasoning", ""),
            last_updated_reasoning=data.get("last_updated_reasoning", ""),
            fullness=data.get("fullness", 0.1),
            spawned_curiosities=data.get("spawned_curiosities", []),
        )

    @classmethod
    def create(
        cls,
        focus: str,
        domain: str,
        reasoning: str,
        fullness: float = 0.1,
        pull: float = 0.5,
    ) -> "Discovery":
        """Create a new discovery with generated ID."""
        now = datetime.now()
        return cls(
            id=generate_curiosity_id("disc"),
            focus=focus,
            domain=domain,
            pull=pull,
            status="sparse",
            created_at=now,
            last_updated=now,
            created_reasoning=reasoning,
            last_updated_reasoning=reasoning,
            fullness=fullness,
        )


@dataclass
class Question(ReceptiveCuriosity):
    """
    Focused inquiry about something specific.

    Question is a seed planted in the soil of discovery.
    It follows a specific thread - "What about this?"

    Examples:
    - "למה הוא משחק לבד?" (Why does he play alone?)
    - "מה קורה במעברים?" (What happens during transitions?)
    - "איך הוא מתקשר?" (How does he communicate?)

    Status progression: open → partial → answered OR evolved
    When substantially answered AND a theory crystallizes → evolves to hypothesis.
    """
    question: str = ""  # The full question text

    # Lineage
    source_discovery: Optional[str] = None  # Discovery ID this came from
    spawned_hypothesis: Optional[str] = None  # Hypothesis ID if evolved
    related_observations: List[str] = field(default_factory=list)  # Observation IDs

    @property
    def curiosity_type(self) -> str:
        return "question"

    def evolve_to_hypothesis(self, hypothesis_id: str, reasoning: str):
        """Mark this question as evolved into a hypothesis."""
        self.spawned_hypothesis = hypothesis_id
        self.status = "evolved"
        self.touch(reasoning)

    def add_related_observation(self, observation_id: str, reasoning: str):
        """Link an observation that addresses this question."""
        if observation_id not in self.related_observations:
            self.related_observations.append(observation_id)
        self.touch(reasoning)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["question"] = self.question
        data["source_discovery"] = self.source_discovery
        data["spawned_hypothesis"] = self.spawned_hypothesis
        data["related_observations"] = self.related_observations
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        return cls(
            id=data["id"],
            focus=data["focus"],
            domain=data["domain"],
            pull=data.get("pull", 0.5),
            status=data.get("status", "open"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            last_updated=datetime.fromisoformat(data["last_updated"]) if isinstance(data.get("last_updated"), str) else data.get("last_updated", datetime.now()),
            created_reasoning=data.get("created_reasoning", ""),
            last_updated_reasoning=data.get("last_updated_reasoning", ""),
            fullness=data.get("fullness", 0.1),
            question=data.get("question", ""),
            source_discovery=data.get("source_discovery"),
            spawned_hypothesis=data.get("spawned_hypothesis"),
            related_observations=data.get("related_observations", []),
        )

    @classmethod
    def create(
        cls,
        focus: str,
        question: str,
        domain: str,
        reasoning: str,
        source_discovery: Optional[str] = None,
        fullness: float = 0.1,
        pull: float = 0.6,
    ) -> "Question":
        """Create a new question with generated ID."""
        now = datetime.now()
        return cls(
            id=generate_curiosity_id("ques"),
            focus=focus,
            domain=domain,
            pull=pull,
            status="open",
            created_at=now,
            last_updated=now,
            created_reasoning=reasoning,
            last_updated_reasoning=reasoning,
            fullness=fullness,
            question=question,
            source_discovery=source_discovery,
        )


@dataclass
class Evidence:
    """
    Evidence for an assertive curiosity (Hypothesis or Pattern).

    Evidence is immutable - a record of what was observed and how it affects confidence.
    Every evidence has full provenance for explainability.
    """
    id: str
    content: str
    effect: str  # "supports" | "contradicts" | "transforms"

    # Temporal
    timestamp: datetime
    session_id: str

    # Provenance (REQUIRED)
    source_observation: str  # Observation ID this came from
    reasoning: str  # Why does this evidence have this effect?

    # Confidence tracking
    confidence_before: float
    confidence_after: float

    @classmethod
    def create(
        cls,
        content: str,
        effect: str,
        session_id: str,
        source_observation: str,
        reasoning: str,
        confidence_before: float,
        confidence_after: float,
    ) -> "Evidence":
        """Create new evidence with generated ID."""
        return cls(
            id=f"evid_{uuid.uuid4().hex[:8]}",
            content=content,
            effect=effect,
            timestamp=datetime.now(),
            session_id=session_id,
            source_observation=source_observation,
            reasoning=reasoning,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "effect": self.effect,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "source_observation": self.source_observation,
            "reasoning": self.reasoning,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        return cls(
            id=data["id"],
            content=data["content"],
            effect=data.get("effect", "supports"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else data.get("timestamp", datetime.now()),
            session_id=data.get("session_id", ""),
            source_observation=data.get("source_observation", ""),
            reasoning=data.get("reasoning", ""),
            confidence_before=data.get("confidence_before", 0.0),
            confidence_after=data.get("confidence_after", 0.0),
        )


@dataclass
class Hypothesis(AssertiveCuriosity):
    """
    Testable theory about the child.

    Hypothesis is a growing plant in the garden.
    It makes a claim that can be supported, contradicted, or transformed.

    Examples:
    - "רגישות חושית משפיעה על ויסות" (Sensory sensitivity affects regulation)
    - "מוזיקה עוזרת לו להירגע" (Music helps him calm down)
    - "מעברים קשים יותר בבקרים" (Transitions harder in mornings)

    IMPORTANT: Theory must be in TENTATIVE language (יכול להיות ש..., נראה ש...)

    Status progression: weak → testing → supported → confirmed
    Can be refuted (contradicting evidence) or transformed (new understanding).
    """
    theory: str = ""  # The testable claim (TENTATIVE language)

    # Video testing
    video_appropriate: bool = False  # Can video test this hypothesis?
    video_value: Optional[str] = None  # calibration | chain | discovery | reframe | relational
    video_value_reason: Optional[str] = None  # Why video would help
    video_requested: bool = False  # Has video been requested?

    # Evidence chain
    evidence: List[Evidence] = field(default_factory=list)

    # Video investigation workflow
    investigation: Optional["InvestigationContext"] = None

    # Lineage
    source_question: Optional[str] = None  # Question ID this evolved from
    contributed_to_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    predecessor: Optional[str] = None  # If transformed from another hypothesis
    successor: Optional[str] = None  # If transformed into another hypothesis

    @property
    def curiosity_type(self) -> str:
        return "hypothesis"

    def add_evidence(self, evidence: Evidence, reasoning: str):
        """Add evidence and update confidence."""
        self.evidence.append(evidence)
        self.confidence = evidence.confidence_after
        self.touch(reasoning)

        # Update status based on confidence
        if self.confidence >= 0.8:
            self.status = "confirmed"
        elif self.confidence >= 0.6:
            self.status = "supported"
        elif self.confidence <= 0.2 and len([e for e in self.evidence if e.effect == "contradicts"]) >= 2:
            self.status = "refuted"
        elif len(self.evidence) > 0:
            self.status = "testing"

    def refute(self, reasoning: str):
        """Mark hypothesis as refuted."""
        self.status = "refuted"
        self.touch(reasoning)

    def transform(self, successor_id: str, reasoning: str):
        """Mark hypothesis as transformed into a new one."""
        self.successor = successor_id
        self.status = "transformed"
        self.touch(reasoning)

    def contribute_to_pattern(self, pattern_id: str, reasoning: str):
        """Record that this hypothesis contributed to a pattern."""
        if pattern_id not in self.contributed_to_patterns:
            self.contributed_to_patterns.append(pattern_id)
        self.touch(reasoning)

    def start_investigation(self):
        """Start a video investigation for this hypothesis."""
        from .models import InvestigationContext
        if self.investigation is None:
            self.investigation = InvestigationContext.create()

    def accept_video(self):
        """Accept video recording for this hypothesis."""
        if self.investigation:
            self.investigation.video_accepted = True
            self.investigation.video_suggested_at = datetime.now()

    def decline_video(self):
        """Decline video recording for this hypothesis."""
        if self.investigation:
            self.investigation.video_declined = True

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["theory"] = self.theory
        data["video_appropriate"] = self.video_appropriate
        data["video_value"] = self.video_value
        data["video_value_reason"] = self.video_value_reason
        data["video_requested"] = self.video_requested
        data["evidence"] = [e.to_dict() for e in self.evidence]
        data["investigation"] = self.investigation.to_dict() if self.investigation else None
        data["source_question"] = self.source_question
        data["contributed_to_patterns"] = self.contributed_to_patterns
        data["predecessor"] = self.predecessor
        data["successor"] = self.successor
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        from .models import InvestigationContext
        evidence = [Evidence.from_dict(e) for e in data.get("evidence", [])]
        investigation = None
        if data.get("investigation"):
            investigation = InvestigationContext.from_dict(data["investigation"])
        return cls(
            id=data["id"],
            focus=data["focus"],
            domain=data["domain"],
            pull=data.get("pull", 0.5),
            status=data.get("status", "weak"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            last_updated=datetime.fromisoformat(data["last_updated"]) if isinstance(data.get("last_updated"), str) else data.get("last_updated", datetime.now()),
            created_reasoning=data.get("created_reasoning", ""),
            last_updated_reasoning=data.get("last_updated_reasoning", ""),
            confidence=data.get("confidence", 0.3),
            theory=data.get("theory", ""),
            video_appropriate=data.get("video_appropriate", False),
            video_value=data.get("video_value"),
            video_value_reason=data.get("video_value_reason"),
            video_requested=data.get("video_requested", False),
            evidence=evidence,
            investigation=investigation,
            source_question=data.get("source_question"),
            contributed_to_patterns=data.get("contributed_to_patterns", []),
            predecessor=data.get("predecessor"),
            successor=data.get("successor"),
        )

    @classmethod
    def create(
        cls,
        focus: str,
        theory: str,
        domain: str,
        reasoning: str,
        source_question: Optional[str] = None,
        confidence: float = 0.3,
        pull: float = 0.6,
        video_appropriate: bool = False,
        video_value: Optional[str] = None,
        video_value_reason: Optional[str] = None,
    ) -> "Hypothesis":
        """Create a new hypothesis with generated ID."""
        now = datetime.now()
        return cls(
            id=generate_curiosity_id("hypo"),
            focus=focus,
            domain=domain,
            pull=pull,
            status="weak",
            created_at=now,
            last_updated=now,
            created_reasoning=reasoning,
            last_updated_reasoning=reasoning,
            confidence=confidence,
            theory=theory,
            video_appropriate=video_appropriate,
            video_value=video_value,
            video_value_reason=video_value_reason,
            source_question=source_question,
        )


@dataclass
class Pattern(AssertiveCuriosity):
    """
    Cross-domain insight about the child.

    Pattern is an ecosystem - emergent order from many thriving hypotheses.
    It connects multiple confirmed hypotheses into a coherent understanding.

    Examples:
    - "רגישות חושית היא המפתח לויסות שלו" (Sensory sensitivity is key to his regulation)
    - "הוא מתפקד הכי טוב דרך משחק" (He functions best through play)
    - "השליטה חשובה לו מאוד" (Control is very important to him)

    Status progression: emerging → solid → foundational
    Can be questioned (when source hypotheses weaken) or dissolved.
    """
    insight: str = ""  # The cross-domain insight

    # Multi-domain
    domains_involved: List[str] = field(default_factory=list)

    # Lineage
    source_hypotheses: List[str] = field(default_factory=list)  # Hypothesis IDs
    spawned_questions: List[str] = field(default_factory=list)  # New questions from pattern
    evidence_chain: List[str] = field(default_factory=list)  # All observation IDs

    @property
    def curiosity_type(self) -> str:
        return "pattern"

    def add_source_hypothesis(self, hypothesis_id: str, reasoning: str):
        """Add a hypothesis that contributes to this pattern."""
        if hypothesis_id not in self.source_hypotheses:
            self.source_hypotheses.append(hypothesis_id)
        self.touch(reasoning)

    def spawn_question(self, question_id: str, reasoning: str):
        """Record a new question spawned from this pattern."""
        if question_id not in self.spawned_questions:
            self.spawned_questions.append(question_id)
        self.touch(reasoning)

    def add_evidence_to_chain(self, observation_id: str):
        """Add observation to evidence chain."""
        if observation_id not in self.evidence_chain:
            self.evidence_chain.append(observation_id)

    def question_pattern(self, reasoning: str):
        """Mark pattern as questioned (when source hypotheses weaken)."""
        self.status = "questioned"
        self.touch(reasoning)

    def dissolve(self, reasoning: str):
        """Dissolve pattern (when evidence no longer supports)."""
        self.status = "dissolved"
        self.touch(reasoning)

    def solidify(self, reasoning: str):
        """Mark pattern as solid."""
        self.status = "solid"
        self.touch(reasoning)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["insight"] = self.insight
        data["domains_involved"] = self.domains_involved
        data["source_hypotheses"] = self.source_hypotheses
        data["spawned_questions"] = self.spawned_questions
        data["evidence_chain"] = self.evidence_chain
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        return cls(
            id=data["id"],
            focus=data["focus"],
            domain=data["domain"],
            pull=data.get("pull", 0.4),
            status=data.get("status", "emerging"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            last_updated=datetime.fromisoformat(data["last_updated"]) if isinstance(data.get("last_updated"), str) else data.get("last_updated", datetime.now()),
            created_reasoning=data.get("created_reasoning", ""),
            last_updated_reasoning=data.get("last_updated_reasoning", ""),
            confidence=data.get("confidence", 0.4),
            insight=data.get("insight", ""),
            domains_involved=data.get("domains_involved", []),
            source_hypotheses=data.get("source_hypotheses", []),
            spawned_questions=data.get("spawned_questions", []),
            evidence_chain=data.get("evidence_chain", []),
        )

    @classmethod
    def create(
        cls,
        focus: str,
        insight: str,
        domains_involved: List[str],
        source_hypotheses: List[str],
        reasoning: str,
        confidence: float = 0.4,
        pull: float = 0.4,
    ) -> "Pattern":
        """Create a new pattern with generated ID."""
        now = datetime.now()
        return cls(
            id=generate_curiosity_id("patt"),
            focus=focus,
            domain=domains_involved[0] if domains_involved else "general",
            pull=pull,
            status="emerging",
            created_at=now,
            last_updated=now,
            created_reasoning=reasoning,
            last_updated_reasoning=reasoning,
            confidence=confidence,
            insight=insight,
            domains_involved=domains_involved,
            source_hypotheses=source_hypotheses,
        )


# =============================================================================
# Type Union and Factory
# =============================================================================

# Type alias for any curiosity
AnyCuriosity = Union[Discovery, Question, Hypothesis, Pattern]


def curiosity_from_dict(data: Dict[str, Any]) -> AnyCuriosity:
    """
    Factory function to create the correct curiosity type from dict.

    Uses the 'type' field to determine which class to instantiate.
    """
    curiosity_type = data.get("type", "discovery")

    type_map = {
        "discovery": Discovery,
        "question": Question,
        "hypothesis": Hypothesis,
        "pattern": Pattern,
    }

    cls = type_map.get(curiosity_type)
    if not cls:
        raise ValueError(f"Unknown curiosity type: {curiosity_type}")

    return cls.from_dict(data)


# =============================================================================
# Lineage Helper
# =============================================================================

@dataclass
class CuriosityLineage:
    """
    Traces the evolution path of a curiosity.

    Used for explainability - shows how understanding evolved.
    """
    curiosity_id: str
    curiosity_type: str
    focus: str

    # Ancestors (where it came from)
    source_discovery: Optional[str] = None
    source_question: Optional[str] = None
    predecessor_hypothesis: Optional[str] = None

    # Descendants (what it spawned)
    spawned_questions: List[str] = field(default_factory=list)
    spawned_hypothesis: Optional[str] = None
    successor_hypothesis: Optional[str] = None
    contributed_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "curiosity_id": self.curiosity_id,
            "curiosity_type": self.curiosity_type,
            "focus": self.focus,
            "source_discovery": self.source_discovery,
            "source_question": self.source_question,
            "predecessor_hypothesis": self.predecessor_hypothesis,
            "spawned_questions": self.spawned_questions,
            "spawned_hypothesis": self.spawned_hypothesis,
            "successor_hypothesis": self.successor_hypothesis,
            "contributed_patterns": self.contributed_patterns,
        }
