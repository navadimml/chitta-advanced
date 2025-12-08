"""
Curiosity Model and Engine

The unified model for what the Gestalt wants to understand.

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
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import TemporalFact, Understanding


@dataclass
class Curiosity:
    """
    Something the Gestalt wants to understand.

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
    activation: float                   # How active right now (0-1)
    certainty: float                    # How confident within this type (0-1)

    # Type-specific fields (used based on type)
    theory: Optional[str] = None        # For hypothesis: the theory to test
    video_appropriate: bool = False     # For hypothesis: can video test this?
    question: Optional[str] = None      # For question: the specific question
    domains_involved: List[str] = field(default_factory=list)  # For pattern: domains connected

    # Common fields
    domain: Optional[str] = None        # Primary developmental domain
    last_activated: datetime = field(default_factory=datetime.now)
    times_explored: int = 0

    # Linkage to exploration cycles
    cycle_id: Optional[str] = None      # If this spawned an exploration cycle

    def copy(self) -> "Curiosity":
        """Create a copy of this curiosity."""
        return Curiosity(
            focus=self.focus,
            type=self.type,
            activation=self.activation,
            certainty=self.certainty,
            theory=self.theory,
            video_appropriate=self.video_appropriate,
            question=self.question,
            domains_involved=list(self.domains_involved),
            domain=self.domain,
            last_activated=self.last_activated,
            times_explored=self.times_explored,
            cycle_id=self.cycle_id,
        )

    def should_spawn_cycle(self) -> bool:
        """Should this curiosity spawn an exploration cycle?"""
        return self.activation > 0.7 and self.times_explored == 0 and self.cycle_id is None

    def mark_explored(self):
        """Mark this curiosity as explored."""
        self.times_explored += 1
        self.last_activated = datetime.now()

    def boost_activation(self, amount: float = 0.1):
        """Boost activation (clamped to 1.0)."""
        self.activation = min(1.0, self.activation + amount)
        self.last_activated = datetime.now()

    def dampen_activation(self, amount: float = 0.1):
        """Dampen activation (clamped to 0.0)."""
        self.activation = max(0.0, self.activation - amount)

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


class CuriosityEngine:
    """
    Manages the Gestalt's curiosities.

    - 5 perpetual curiosities (always present)
    - Dynamic curiosities (spawned from conversation)
    - Activation rises/falls based on evidence and time
    """

    # The five perpetual curiosities - always present
    PERPETUAL_TEMPLATES = [
        {
            "focus": "מי הילד הזה?",
            "type": "discovery",
            "activation": 0.8,
            "certainty": 0.1,
            "domain": "essence",
        },
        {
            "focus": "מה הוא אוהב?",
            "type": "discovery",
            "activation": 0.6,
            "certainty": 0.1,
            "domain": "strengths",
        },
        {
            "focus": "מה ההקשר שלו?",
            "type": "discovery",
            "activation": 0.4,
            "certainty": 0.1,
            "domain": "context",
        },
        {
            "focus": "מה הביא אותם לכאן?",
            "type": "question",
            "activation": 0.5,
            "certainty": 0.1,
            "question": "מה הדאגות שהביאו את המשפחה לחפש עזרה?",
            "domain": "concerns",
        },
        {
            "focus": "אילו דפוסים מתגלים?",
            "type": "pattern",
            "activation": 0.3,
            "certainty": 0.1,
            "domains_involved": [],
        },
    ]

    # Time decay rate (activation loss per day)
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
                activation=t["activation"],
                certainty=t["certainty"],
                domain=t.get("domain"),
                question=t.get("question"),
                domains_involved=t.get("domains_involved", []),
            )
            for t in self.PERPETUAL_TEMPLATES
        ]
        self._dynamic: List[Curiosity] = []

    def get_active(self, understanding: Optional["Understanding"] = None) -> List[Curiosity]:
        """
        Get all curiosities sorted by activation.

        Returns copies with updated activation values.
        """
        all_curiosities = [c.copy() for c in self._perpetual] + [c.copy() for c in self._dynamic]

        for c in all_curiosities:
            c.activation = self._calculate_activation(c, understanding)

        return sorted(all_curiosities, key=lambda c: c.activation, reverse=True)

    def get_top(self, n: int = 5, understanding: Optional["Understanding"] = None) -> List[Curiosity]:
        """Get top N curiosities by activation."""
        return self.get_active(understanding)[:n]

    def _calculate_activation(
        self,
        curiosity: Curiosity,
        understanding: Optional["Understanding"] = None
    ) -> float:
        """
        Calculate activation based on gaps, evidence, time.

        Factors:
        - Base activation
        - Time decay (loses activation over time without activity)
        - Gap boost (more gaps in domain = more activation)
        - High certainty dampening (satisfied curiosities are less active)
        """
        base = curiosity.activation

        # Time decay (DECAY_RATE_PER_DAY per day without activity)
        days_since = (datetime.now() - curiosity.last_activated).days
        base -= days_since * self.DECAY_RATE_PER_DAY

        # Gap boost (more gaps in this domain = more activation)
        if curiosity.domain and understanding:
            gaps = self._count_domain_gaps(curiosity.domain, understanding)
            base += min(gaps * self.GAP_BOOST_PER_ITEM, self.GAP_BOOST_MAX)

        # High certainty dampens activation (we're satisfied)
        if curiosity.certainty > self.HIGH_CERTAINTY_THRESHOLD:
            base -= self.HIGH_CERTAINTY_DAMPEN

        return max(0.0, min(1.0, base))

    def _count_domain_gaps(self, domain: str, understanding: "Understanding") -> int:
        """
        Count gaps in a domain.

        This is a heuristic - domains with fewer facts have more gaps.
        """
        if not understanding or not hasattr(understanding, 'facts'):
            return 3  # Default to moderate gaps

        domain_facts = [f for f in understanding.facts if getattr(f, 'domain', None) == domain]

        # Fewer facts = more gaps (inverse relationship)
        # 0 facts = 5 gaps, 1-2 facts = 3 gaps, 3-5 facts = 1 gap, 6+ facts = 0 gaps
        fact_count = len(domain_facts)
        if fact_count == 0:
            return 5
        elif fact_count <= 2:
            return 3
        elif fact_count <= 5:
            return 1
        else:
            return 0

    def add_curiosity(self, curiosity: Curiosity):
        """Add a new dynamic curiosity."""
        # Check for duplicates by focus
        for existing in self._dynamic:
            if existing.focus.lower() == curiosity.focus.lower():
                # Boost existing instead of adding duplicate
                existing.boost_activation(0.2)
                return

        self._dynamic.append(curiosity)

    def remove_curiosity(self, focus: str):
        """Remove a dynamic curiosity by focus."""
        self._dynamic = [c for c in self._dynamic if c.focus != focus]

    def on_fact_learned(self, fact: "TemporalFact"):
        """Boost activation for related curiosities when a fact is learned."""
        domain = getattr(fact, 'domain', None)
        if not domain:
            return

        for c in self._dynamic + self._perpetual:
            if c.domain == domain:
                c.boost_activation(0.1)

            # Also check pattern curiosities
            if c.type == "pattern" and domain in c.domains_involved:
                c.boost_activation(0.15)

    def on_evidence_added(self, curiosity_focus: str, effect: str):
        """Update certainty based on evidence."""
        for c in self._dynamic:
            if c.focus == curiosity_focus:
                c.update_certainty(effect)
                c.boost_activation(0.05)  # Small activation boost for activity
                break

    def on_domain_touched(self, domain: str):
        """Called when conversation touches a domain."""
        for c in self._perpetual + self._dynamic:
            if c.domain == domain:
                c.boost_activation(0.05)

    def get_gaps(self) -> List[str]:
        """
        What do we know we don't know?

        Returns questions/focuses from curiosities that are:
        - Active (activation > 0.5)
        - Uncertain (certainty < 0.5)
        """
        gaps = []
        for c in self._perpetual + self._dynamic:
            if c.activation > 0.5 and c.certainty < 0.5:
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

    def link_to_cycle(self, curiosity_focus: str, cycle_id: str):
        """Link a curiosity to an exploration cycle."""
        for c in self._dynamic:
            if c.focus == curiosity_focus:
                c.cycle_id = cycle_id
                c.mark_explored()
                break

    def to_dict(self) -> dict:
        """Serialize for persistence."""
        return {
            "dynamic": [
                {
                    "focus": c.focus,
                    "type": c.type,
                    "activation": c.activation,
                    "certainty": c.certainty,
                    "theory": c.theory,
                    "video_appropriate": c.video_appropriate,
                    "question": c.question,
                    "domains_involved": c.domains_involved,
                    "domain": c.domain,
                    "last_activated": c.last_activated.isoformat(),
                    "times_explored": c.times_explored,
                    "cycle_id": c.cycle_id,
                }
                for c in self._dynamic
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CuriosityEngine":
        """Deserialize from persistence."""
        engine = cls()

        for c_data in data.get("dynamic", []):
            last_activated = c_data.get("last_activated")
            if isinstance(last_activated, str):
                last_activated = datetime.fromisoformat(last_activated)
            else:
                last_activated = datetime.now()

            curiosity = Curiosity(
                focus=c_data["focus"],
                type=c_data["type"],
                activation=c_data.get("activation", 0.5),
                certainty=c_data.get("certainty", 0.3),
                theory=c_data.get("theory"),
                video_appropriate=c_data.get("video_appropriate", False),
                question=c_data.get("question"),
                domains_involved=c_data.get("domains_involved", []),
                domain=c_data.get("domain"),
                last_activated=last_activated,
                times_explored=c_data.get("times_explored", 0),
                cycle_id=c_data.get("cycle_id"),
            )
            engine._dynamic.append(curiosity)

        return engine


# Factory functions for creating curiosities

def create_discovery(focus: str, domain: str, activation: float = 0.6) -> Curiosity:
    """Create a discovery-type curiosity."""
    return Curiosity(
        focus=focus,
        type="discovery",
        activation=activation,
        certainty=0.1,
        domain=domain,
    )


def create_question(
    focus: str,
    question: str,
    domain: Optional[str] = None,
    activation: float = 0.6
) -> Curiosity:
    """Create a question-type curiosity."""
    return Curiosity(
        focus=focus,
        type="question",
        activation=activation,
        certainty=0.1,
        question=question,
        domain=domain,
    )


def create_hypothesis(
    focus: str,
    theory: str,
    domain: str,
    video_appropriate: bool = True,
    activation: float = 0.7,
    certainty: float = 0.3,
) -> Curiosity:
    """Create a hypothesis-type curiosity."""
    return Curiosity(
        focus=focus,
        type="hypothesis",
        activation=activation,
        certainty=certainty,
        theory=theory,
        video_appropriate=video_appropriate,
        domain=domain,
    )


def create_pattern(
    focus: str,
    domains_involved: List[str],
    activation: float = 0.5,
    certainty: float = 0.2,
) -> Curiosity:
    """Create a pattern-type curiosity."""
    return Curiosity(
        focus=focus,
        type="pattern",
        activation=activation,
        certainty=certainty,
        domains_involved=domains_involved,
    )
