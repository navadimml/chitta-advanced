"""
Curiosity Model and Curiosities Manager

The unified model for what Darshan wants to understand.

DESIGN PRINCIPLES:
- One model serves all four exploration modes
- Type and certainty are INDEPENDENT
- 5 perpetual curiosities always present
- Dynamic curiosities spawn from conversation

TYPE AND CERTAINTY:
| Type       | Certainty 0.2              | Certainty 0.8                |
|------------|----------------------------|------------------------------|
| discovery  | Just starting to see       | Rich picture emerging        |
| question   | No clues yet               | Almost answered              |
| hypothesis | Weak theory                | Nearly confirmed             |
| pattern    | Vague connection           | Clear cross-cutting theme    |
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .models import TemporalFact, Understanding, Evidence, VideoScenario


@dataclass
class InvestigationContext:
    """
    Attached to Curiosity when actively investigating.

    Contains all evidence collection and video workflow state.
    This replaces the old Exploration class.
    """
    id: str
    status: str  # "active" | "complete" | "stale"
    started_at: datetime = field(default_factory=datetime.now)

    # Evidence collection
    evidence: List["Evidence"] = field(default_factory=list)

    # Video workflow
    video_accepted: bool = False
    video_declined: bool = False
    video_suggested_at: Optional[datetime] = None
    video_scenarios: List["VideoScenario"] = field(default_factory=list)
    guidelines_status: Optional[str] = None  # "generating" | "ready" | "error"

    @classmethod
    def create(cls) -> "InvestigationContext":
        """Create a new investigation context."""
        return cls(
            id=f"inv_{uuid.uuid4().hex[:8]}",
            status="active",
            started_at=datetime.now(),
        )

    def add_evidence(self, evidence: "Evidence"):
        """Add evidence to this investigation."""
        self.evidence.append(evidence)

    def accept_video(self):
        """Mark video as accepted."""
        self.video_accepted = True
        self.video_declined = False

    def decline_video(self):
        """Mark video as declined."""
        self.video_declined = True
        self.video_accepted = False

    def can_suggest_video(self, video_appropriate: bool) -> bool:
        """Check if video can be suggested for this investigation."""
        return (
            video_appropriate and
            not self.video_accepted and
            not self.video_declined and
            self.status == "active"
        )

    def get_scenario(self, scenario_id: str) -> Optional["VideoScenario"]:
        """Get a video scenario by ID."""
        for s in self.video_scenarios:
            if s.id == scenario_id:
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for persistence."""
        return {
            "id": self.id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "evidence": [
                {
                    "content": e.content,
                    "effect": e.effect,
                    "source": e.source,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self.evidence
            ],
            "video_accepted": self.video_accepted,
            "video_declined": self.video_declined,
            "video_suggested_at": self.video_suggested_at.isoformat() if self.video_suggested_at else None,
            "video_scenarios": [s.to_dict() for s in self.video_scenarios],
            "guidelines_status": self.guidelines_status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestigationContext":
        """Deserialize from persistence."""
        from .models import Evidence, VideoScenario

        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        else:
            started_at = datetime.now()

        video_suggested_at = data.get("video_suggested_at")
        if isinstance(video_suggested_at, str):
            video_suggested_at = datetime.fromisoformat(video_suggested_at)

        evidence_list = []
        for e_data in data.get("evidence", []):
            timestamp = e_data.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            else:
                timestamp = datetime.now()

            evidence_list.append(Evidence(
                content=e_data["content"],
                effect=e_data.get("effect", "supports"),
                source=e_data.get("source", "conversation"),
                timestamp=timestamp,
            ))

        video_scenarios = []
        for s_data in data.get("video_scenarios", []):
            video_scenarios.append(VideoScenario.from_dict(s_data))

        return cls(
            id=data["id"],
            status=data.get("status", "active"),
            started_at=started_at,
            evidence=evidence_list,
            video_accepted=data.get("video_accepted", False),
            video_declined=data.get("video_declined", False),
            video_suggested_at=video_suggested_at,
            video_scenarios=video_scenarios,
            guidelines_status=data.get("guidelines_status"),
        )


@dataclass
class Curiosity:
    """
    Something Darshan wants to understand.

    One model serves all four exploration modes:
    - discovery: Open receiving ("Who is this child?")
    - question: Following a thread ("What triggers meltdowns?")
    - hypothesis: Testing a theory ("Music helps him regulate")
    - pattern: Connecting dots across domains ("Sensory input is key")

    Type and certainty are INDEPENDENT:
    - Type = what kind of exploration activity
    - Certainty = how confident within that activity

    You can have a weak hypothesis (certainty=0.3) or a strong discovery (certainty=0.8).
    """
    focus: str                          # What we're curious about
    type: str                           # "discovery" | "question" | "hypothesis" | "pattern"
    pull: float                         # How strongly it draws attention (0-1)
    certainty: float                    # How confident within this type (0-1)

    # Type-specific fields (used based on type)
    theory: Optional[str] = None        # For hypothesis: the theory to test
    video_appropriate: bool = False     # For hypothesis: can video test this?
    question: Optional[str] = None      # For question: the specific question
    domains_involved: List[str] = field(default_factory=list)  # For pattern: domains connected

    # Video value fields (LLM-determined)
    video_value: Optional[str] = None   # calibration | chain | discovery | reframe | relational
    video_value_reason: Optional[str] = None  # Why video would help

    # Common fields
    domain: Optional[str] = None        # Primary developmental domain
    last_activated: datetime = field(default_factory=datetime.now)
    times_explored: int = 0

    # Lifecycle status
    status: str = "wondering"  # "wondering" | "investigating" | "understood" | "dormant"

    # Investigation context (None = wondering, has value = investigating/understood)
    investigation: Optional[InvestigationContext] = None

    def copy(self) -> "Curiosity":
        """Create a copy of this curiosity."""
        return Curiosity(
            focus=self.focus,
            type=self.type,
            pull=self.pull,
            certainty=self.certainty,
            theory=self.theory,
            video_appropriate=self.video_appropriate,
            question=self.question,
            domains_involved=list(self.domains_involved),
            video_value=self.video_value,
            video_value_reason=self.video_value_reason,
            domain=self.domain,
            last_activated=self.last_activated,
            times_explored=self.times_explored,
            status=self.status,
            investigation=self.investigation,  # Shallow copy - same investigation context
        )

    def should_start_investigation(self) -> bool:
        """Should this curiosity start an investigation?"""
        return (
            self.status == "wondering" and
            self.pull > 0.7 and
            self.investigation is None
        )

    def start_investigation(self) -> InvestigationContext:
        """Start investigating this curiosity."""
        if self.investigation is not None:
            return self.investigation

        self.investigation = InvestigationContext.create()
        self.status = "investigating"
        self.last_activated = datetime.now()
        self.times_explored += 1
        return self.investigation

    def mark_explored(self):
        """Mark this curiosity as explored."""
        self.times_explored += 1
        self.last_activated = datetime.now()

    def mark_understood(self):
        """Mark this curiosity as understood (investigation complete)."""
        self.status = "understood"
        if self.investigation:
            self.investigation.status = "complete"
        self.last_activated = datetime.now()

    def mark_dormant(self):
        """Mark this curiosity as dormant (lost interest)."""
        self.status = "dormant"
        self.last_activated = datetime.now()

    def add_evidence(self, evidence: "Evidence"):
        """Add evidence to this curiosity's investigation."""
        if self.investigation is None:
            self.start_investigation()
        self.investigation.add_evidence(evidence)
        self.last_activated = datetime.now()

    def can_suggest_video(self) -> bool:
        """
        Check if video can be suggested for this curiosity.

        Video is suggestable when:
        1. Investigating hypothesis with video_appropriate=True
        2. Wondering with video_value set and high pull
        3. Pattern with high pull and video_appropriate
        """
        # Already declined or accepted
        if self.investigation:
            if self.investigation.video_accepted or self.investigation.video_declined:
                return False

        # Investigating hypothesis
        if self.status == "investigating" and self.video_appropriate:
            return True

        # Wondering with video value and high pull
        if self.status == "wondering" and self.video_value is not None and self.pull > 0.7:
            return True

        # Pattern with high pull
        if self.type == "pattern" and self.pull > 0.8 and self.video_appropriate:
            return True

        return False

    def accept_video(self):
        """Accept video suggestion for this curiosity."""
        if self.investigation is None:
            self.start_investigation()
        self.investigation.accept_video()
        self.last_activated = datetime.now()

    def decline_video(self):
        """Decline video suggestion for this curiosity."""
        if self.investigation is None:
            self.start_investigation()
        self.investigation.decline_video()
        self.last_activated = datetime.now()

    @property
    def investigation_id(self) -> Optional[str]:
        """Get investigation ID if investigation exists."""
        return self.investigation.id if self.investigation else None

    def boost_pull(self, amount: float = 0.1):
        """Boost pull (clamped to 1.0)."""
        self.pull = min(1.0, self.pull + amount)
        self.last_activated = datetime.now()

    def dampen_pull(self, amount: float = 0.1):
        """Dampen pull (clamped to 0.0)."""
        self.pull = max(0.0, self.pull - amount)

    def update_certainty(self, effect: str):
        """
        Update certainty based on evidence effect.

        effect: "supports" | "contradicts" | "transforms"
        """
        if effect == "supports":
            self.certainty = min(1.0, self.certainty + 0.1)
        elif effect == "contradicts":
            self.certainty = max(0.0, self.certainty - 0.15)
        elif effect == "transforms":
            # Transforms resets certainty - we're exploring something new
            self.certainty = 0.4
        self.last_activated = datetime.now()


class Curiosities:
    """
    Manages Darshan's curiosities.

    - 5 perpetual curiosities (always present)
    - Dynamic curiosities (spawned from conversation)
    - Pull rises/falls based on evidence and time
    """

    # Perpetual curiosities - always present
    # Core understanding (5 original) + Clinical background (3 new)
    PERPETUAL_TEMPLATES = [
        # === Core Understanding ===
        {
            "focus": "מי הילד הזה?",
            "type": "discovery",
            "pull": 0.8,
            "certainty": 0.1,
            "domain": "essence",
        },
        {
            "focus": "מה הוא אוהב?",
            "type": "discovery",
            "pull": 0.6,
            "certainty": 0.1,
            "domain": "strengths",
        },
        {
            "focus": "מה ההקשר שלו?",
            "type": "discovery",
            "pull": 0.4,
            "certainty": 0.1,
            "domain": "context",
        },
        {
            "focus": "מה הביא אותם לכאן?",
            "type": "question",
            "pull": 0.5,
            "certainty": 0.1,
            "question": "מה הדאגות שהביאו את המשפחה לחפש עזרה?",
            "domain": "concerns",
        },
        {
            "focus": "אילו דפוסים מתגלים?",
            "type": "pattern",
            "pull": 0.3,
            "certainty": 0.1,
            "domains_involved": [],
        },
        # === Clinical Background (for Letters) ===
        {
            "focus": "מה היה קודם?",
            "type": "discovery",
            "pull": 0.5,
            "certainty": 0.1,
            "domain": "birth_history",
        },
        {
            "focus": "איך התפתח עד עכשיו?",
            "type": "discovery",
            "pull": 0.4,
            "certainty": 0.1,
            "domain": "milestones",
        },
        {
            "focus": "מה קורה בשינה ובאוכל?",
            "type": "question",
            "pull": 0.3,
            "certainty": 0.1,
            "question": "איך נראים השינה והאכילה?",
            "domain": "sleep",
        },
    ]

    # Time decay rate (pull loss per day)
    DECAY_RATE_PER_DAY = 0.02

    # Gap boost per missing piece (capped)
    GAP_BOOST_PER_ITEM = 0.1
    GAP_BOOST_MAX = 0.3

    # High certainty dampening
    HIGH_CERTAINTY_THRESHOLD = 0.7
    HIGH_CERTAINTY_DAMPEN = 0.2

    def __init__(self):
        """Initialize with perpetual curiosities."""
        self._perpetual: List[Curiosity] = [
            Curiosity(
                focus=t["focus"],
                type=t["type"],
                pull=t["pull"],
                certainty=t["certainty"],
                domain=t.get("domain"),
                question=t.get("question"),
                domains_involved=t.get("domains_involved", []),
            )
            for t in self.PERPETUAL_TEMPLATES
        ]
        self._dynamic: List[Curiosity] = []

        # Baseline video request (for discovery before hypotheses form)
        # This is stored here but managed by Darshan
        self._baseline_video_requested: bool = False

    def get_active(self, understanding: Optional["Understanding"] = None) -> List[Curiosity]:
        """
        Get all curiosities sorted by pull.

        Returns copies with updated pull values.
        """
        all_curiosities = [c.copy() for c in self._perpetual] + [c.copy() for c in self._dynamic]

        for c in all_curiosities:
            c.pull = self._calculate_pull(c, understanding)

        return sorted(all_curiosities, key=lambda c: c.pull, reverse=True)

    def get_top(self, n: int = 5, understanding: Optional["Understanding"] = None) -> List[Curiosity]:
        """Get top N curiosities by pull."""
        return self.get_active(understanding)[:n]

    def _calculate_pull(
        self,
        curiosity: Curiosity,
        understanding: Optional["Understanding"] = None
    ) -> float:
        """
        Calculate pull based on gaps, evidence, time.

        Factors:
        - Base pull
        - Time decay (loses pull over time without activity)
        - Gap boost (more gaps in domain = more pull)
        - High certainty dampening (satisfied curiosities pull less)
        """
        base = curiosity.pull

        # Time decay (DECAY_RATE_PER_DAY per day without activity)
        days_since = (datetime.now() - curiosity.last_activated).days
        base -= days_since * self.DECAY_RATE_PER_DAY

        # Gap boost (more gaps in this domain = more pull)
        if curiosity.domain and understanding:
            gaps = self._count_domain_gaps(curiosity.domain, understanding)
            base += min(gaps * self.GAP_BOOST_PER_ITEM, self.GAP_BOOST_MAX)

        # High certainty dampens pull (we're satisfied)
        if curiosity.certainty > self.HIGH_CERTAINTY_THRESHOLD:
            base -= self.HIGH_CERTAINTY_DAMPEN

        return max(0.0, min(1.0, base))

    # Clinical domains that are critical for Letters
    CLINICAL_DOMAINS = ["birth_history", "milestones", "sleep", "feeding", "play", "medical"]

    def _count_domain_gaps(self, domain: str, understanding: "Understanding") -> int:
        """
        Count gaps in a domain.

        This is a heuristic - domains with fewer observations have more gaps.
        Clinical domains (for Letters) have higher baseline gaps.
        """
        if not understanding or not hasattr(understanding, 'observations'):
            return 3  # Default to moderate gaps

        domain_observations = [f for f in understanding.observations if getattr(f, 'domain', None) == domain]
        observation_count = len(domain_observations)

        # Clinical domains are more important when empty - Letters need this info
        if domain in self.CLINICAL_DOMAINS:
            # Clinical domains: 0 obs = 5 gaps, 1 obs = 3 gaps, 2+ obs = 1 gap
            if observation_count == 0:
                return 5
            elif observation_count == 1:
                return 3
            else:
                return 1

        # Regular domains: fewer observations = more gaps (inverse relationship)
        # 0 obs = 5 gaps, 1-2 obs = 3 gaps, 3-5 obs = 1 gap, 6+ obs = 0 gaps
        if observation_count == 0:
            return 5
        elif observation_count <= 2:
            return 3
        elif observation_count <= 5:
            return 1
        else:
            return 0

    def add_curiosity(self, curiosity: Curiosity):
        """Add a new dynamic curiosity."""
        # Check for duplicates by focus
        for existing in self._dynamic:
            if existing.focus.lower() == curiosity.focus.lower():
                # Boost existing instead of adding duplicate
                existing.boost_pull(0.2)
                return

        self._dynamic.append(curiosity)

    def remove_curiosity(self, focus: str):
        """Remove a dynamic curiosity by focus."""
        self._dynamic = [c for c in self._dynamic if c.focus != focus]

    def on_observation_learned(self, observation: "TemporalFact"):
        """Boost pull for related curiosities when an observation is learned."""
        domain = getattr(observation, 'domain', None)
        if not domain:
            return

        for c in self._dynamic + self._perpetual:
            if c.domain == domain:
                c.boost_pull(0.1)

            # Also check pattern curiosities
            if c.type == "pattern" and domain in c.domains_involved:
                c.boost_pull(0.15)

    def on_evidence_added(self, curiosity_focus: str, effect: str):
        """Update certainty based on evidence."""
        for c in self._dynamic:
            if c.focus == curiosity_focus:
                c.update_certainty(effect)
                c.boost_pull(0.05)  # Small pull boost for activity
                break

    def on_domain_touched(self, domain: str):
        """Called when conversation touches a domain."""
        for c in self._perpetual + self._dynamic:
            if c.domain == domain:
                c.boost_pull(0.05)

    def get_gaps(self) -> List[str]:
        """
        What do we know we don't know?

        Returns questions/focuses from curiosities that are:
        - Active (pull > 0.5)
        - Uncertain (certainty < 0.5)
        """
        gaps = []
        for c in self._perpetual + self._dynamic:
            if c.pull > 0.5 and c.certainty < 0.5:
                if c.type == "question" and c.question:
                    gaps.append(c.question)
                else:
                    gaps.append(c.focus)

        return gaps[:5]  # Return top 5 gaps

    def get_hypotheses(self) -> List[Curiosity]:
        """Get all hypothesis-type curiosities."""
        return [c for c in self._dynamic if c.type == "hypothesis"]

    def get_video_appropriate_hypotheses(self) -> List[Curiosity]:
        """Get hypotheses that can be tested with video."""
        return [c for c in self._dynamic if c.type == "hypothesis" and c.video_appropriate]

    def get_curiosities_with_video_value(self) -> List[Curiosity]:
        """Get curiosities where video would add value (any type, not just hypothesis)."""
        return [c for c in self._dynamic if c.video_value is not None]

    def find_curiosity_by_domains(self, domains: List[str]) -> Optional[Curiosity]:
        """
        Find an existing pattern curiosity that involves these domains.

        Used to prevent spawning duplicate pattern curiosities when
        cross-domain stories are captured.
        """
        if len(domains) < 2:
            return None

        domain_set = set(domains)
        for c in self._dynamic:
            if c.type == "pattern" and c.domains_involved:
                # Check if there's significant overlap
                overlap = domain_set.intersection(set(c.domains_involved))
                if len(overlap) >= 2:  # At least 2 domains in common
                    return c
        return None

    def should_suggest_baseline_video(self, message_count: int) -> bool:
        """
        Should we suggest baseline video?

        Simple heuristic:
        - Not already requested
        - After some rapport (message 3+)
        - Before heavy theorizing (message <15)
        - Few hypotheses formed
        """
        if self._baseline_video_requested:
            return False  # Already suggested

        if message_count < 3 or message_count > 15:
            return False

        hypothesis_count = len([c for c in self._dynamic if c.type == "hypothesis"])
        return hypothesis_count < 3

    def mark_baseline_video_requested(self):
        """Mark that baseline video has been requested."""
        self._baseline_video_requested = True

    def start_investigation(self, curiosity_focus: str) -> Optional[InvestigationContext]:
        """Start investigation for a curiosity by focus."""
        for c in self._dynamic:
            if c.focus == curiosity_focus:
                return c.start_investigation()
        return None

    def get_investigating(self) -> List[Curiosity]:
        """Get all curiosities that are currently investigating."""
        return [c for c in self._dynamic if c.status == "investigating"]

    def get_curiosity_by_investigation_id(self, investigation_id: str) -> Optional[Curiosity]:
        """Find curiosity by its investigation ID."""
        for c in self._dynamic:
            if c.investigation and c.investigation.id == investigation_id:
                return c
        return None

    def get_video_suggestable(self) -> List[Curiosity]:
        """Get curiosities where video can be suggested."""
        return [c for c in self._dynamic if c.can_suggest_video()]

    def to_dict(self) -> dict:
        """Serialize for persistence."""
        dynamic_list = []
        for c in self._dynamic:
            c_data = {
                "focus": c.focus,
                "type": c.type,
                "pull": c.pull,
                "certainty": c.certainty,
                "theory": c.theory,
                "video_appropriate": c.video_appropriate,
                "video_value": c.video_value,
                "video_value_reason": c.video_value_reason,
                "question": c.question,
                "domains_involved": c.domains_involved,
                "domain": c.domain,
                "last_activated": c.last_activated.isoformat(),
                "times_explored": c.times_explored,
                "status": c.status,
            }
            # Serialize investigation if present
            if c.investigation:
                c_data["investigation"] = c.investigation.to_dict()
            dynamic_list.append(c_data)

        return {
            "dynamic": dynamic_list,
            "baseline_video_requested": self._baseline_video_requested,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Curiosities":
        """Deserialize from persistence."""
        curiosities = cls()

        for c_data in data.get("dynamic", []):
            last_activated = c_data.get("last_activated")
            if isinstance(last_activated, str):
                last_activated = datetime.fromisoformat(last_activated)
            else:
                last_activated = datetime.now()

            # Support both old "activation" and new "pull" keys
            pull_value = c_data.get("pull", c_data.get("activation", 0.5))

            # Deserialize investigation if present
            investigation = None
            if c_data.get("investigation"):
                investigation = InvestigationContext.from_dict(c_data["investigation"])

            curiosity = Curiosity(
                focus=c_data["focus"],
                type=c_data["type"],
                pull=pull_value,
                certainty=c_data.get("certainty", 0.3),
                theory=c_data.get("theory"),
                video_appropriate=c_data.get("video_appropriate", False),
                video_value=c_data.get("video_value"),
                video_value_reason=c_data.get("video_value_reason"),
                question=c_data.get("question"),
                domains_involved=c_data.get("domains_involved", []),
                domain=c_data.get("domain"),
                last_activated=last_activated,
                times_explored=c_data.get("times_explored", 0),
                status=c_data.get("status", "wondering"),
                investigation=investigation,
            )
            curiosities._dynamic.append(curiosity)

        # Restore baseline video state
        curiosities._baseline_video_requested = data.get("baseline_video_requested", False)

        return curiosities


# Factory functions for creating curiosities

def create_discovery(focus: str, domain: str, pull: float = 0.6) -> Curiosity:
    """Create a discovery-type curiosity."""
    return Curiosity(
        focus=focus,
        type="discovery",
        pull=pull,
        certainty=0.1,
        domain=domain,
    )


def create_question(
    focus: str,
    question: str,
    domain: Optional[str] = None,
    pull: float = 0.6
) -> Curiosity:
    """Create a question-type curiosity."""
    return Curiosity(
        focus=focus,
        type="question",
        pull=pull,
        certainty=0.1,
        question=question,
        domain=domain,
    )


def create_hypothesis(
    focus: str,
    theory: str,
    domain: str,
    video_appropriate: bool = True,
    video_value: Optional[str] = None,
    video_value_reason: Optional[str] = None,
    pull: float = 0.7,
    certainty: float = 0.3,
) -> Curiosity:
    """Create a hypothesis-type curiosity."""
    return Curiosity(
        focus=focus,
        type="hypothesis",
        pull=pull,
        certainty=certainty,
        theory=theory,
        video_appropriate=video_appropriate,
        video_value=video_value,
        video_value_reason=video_value_reason,
        domain=domain,
    )


def create_pattern(
    focus: str,
    domains_involved: List[str],
    pull: float = 0.5,
    certainty: float = 0.2,
) -> Curiosity:
    """Create a pattern-type curiosity."""
    return Curiosity(
        focus=focus,
        type="pattern",
        pull=pull,
        certainty=certainty,
        domains_involved=domains_involved,
    )
