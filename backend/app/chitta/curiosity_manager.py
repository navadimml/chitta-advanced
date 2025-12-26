"""
Curiosity Manager - Type-Aware Curiosity Management

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module provides a manager for all curiosity types (Discovery, Question,
Hypothesis, Pattern). It handles:
- Type-specific storage and retrieval
- Cross-type queries (get by focus, get active)
- Lineage tracking (evolution chains)
- Serialization/deserialization

RESPONSIBILITIES:
- Manage curiosities by type
- Route operations to correct type
- Track lineage/evolution
- Serialize/deserialize state

NOT RESPONSIBILITIES (handled elsewhere):
- Decay: handled by DecayManager
- Events: handled by EventRecorder
- Cascades: handled by CascadeHandler
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Iterator
import json

from .curiosity_types import (
    BaseCuriosity,
    ReceptiveCuriosity,
    AssertiveCuriosity,
    Discovery,
    Question,
    Hypothesis,
    Pattern,
    DISCOVERY_STATUSES,
    QUESTION_STATUSES,
    HYPOTHESIS_STATUSES,
    PATTERN_STATUSES,
)


@dataclass
class CuriosityLineage:
    """Trace the evolution path of a curiosity."""
    curiosity_id: str
    curiosity_type: str
    focus: str
    ancestors: List[str]  # IDs of curiosities this evolved from
    descendants: List[str]  # IDs of curiosities that evolved from this
    related_patterns: List[str]  # Patterns this contributed to


class CuriosityManager:
    """
    Manages all curiosity types.

    Provides unified interface for working with the type hierarchy
    while maintaining type-specific behavior.
    """

    def __init__(self):
        """Initialize empty manager."""
        self._discoveries: Dict[str, Discovery] = {}
        self._questions: Dict[str, Question] = {}
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._patterns: Dict[str, Pattern] = {}

        # Index by focus for quick lookup
        self._by_focus: Dict[str, str] = {}  # focus -> id

    # =========================================================================
    # Add/Remove
    # =========================================================================

    def add(self, curiosity: BaseCuriosity) -> None:
        """
        Add a curiosity to the manager.

        Routes to the correct type-specific storage.
        """
        # Store by type
        if isinstance(curiosity, Discovery):
            self._discoveries[curiosity.id] = curiosity
        elif isinstance(curiosity, Question):
            self._questions[curiosity.id] = curiosity
        elif isinstance(curiosity, Hypothesis):
            self._hypotheses[curiosity.id] = curiosity
        elif isinstance(curiosity, Pattern):
            self._patterns[curiosity.id] = curiosity
        else:
            raise ValueError(f"Unknown curiosity type: {type(curiosity)}")

        # Index by focus
        self._by_focus[curiosity.focus] = curiosity.id

    def remove(self, curiosity_id: str) -> Optional[BaseCuriosity]:
        """Remove a curiosity by ID. Returns the removed curiosity or None."""
        for store in [self._discoveries, self._questions, self._hypotheses, self._patterns]:
            if curiosity_id in store:
                curiosity = store.pop(curiosity_id)
                # Remove from focus index
                if curiosity.focus in self._by_focus:
                    del self._by_focus[curiosity.focus]
                return curiosity
        return None

    def remove_by_focus(self, focus: str) -> Optional[BaseCuriosity]:
        """Remove a curiosity by focus. Returns the removed curiosity or None."""
        curiosity_id = self._by_focus.get(focus)
        if curiosity_id:
            return self.remove(curiosity_id)
        return None

    # =========================================================================
    # Retrieval
    # =========================================================================

    def get_by_id(self, curiosity_id: str) -> Optional[BaseCuriosity]:
        """Get a curiosity by ID, searching all types."""
        for store in [self._discoveries, self._questions, self._hypotheses, self._patterns]:
            if curiosity_id in store:
                return store[curiosity_id]
        return None

    def get_by_focus(self, focus: str) -> Optional[BaseCuriosity]:
        """Get a curiosity by focus."""
        curiosity_id = self._by_focus.get(focus)
        if curiosity_id:
            return self.get_by_id(curiosity_id)
        return None

    def get_by_type(self, curiosity_type: str) -> List[BaseCuriosity]:
        """Get all curiosities of a specific type."""
        type_map = {
            "discovery": self._discoveries,
            "question": self._questions,
            "hypothesis": self._hypotheses,
            "pattern": self._patterns,
        }
        store = type_map.get(curiosity_type, {})
        return list(store.values())

    def get_all(self) -> List[BaseCuriosity]:
        """Get all curiosities across all types."""
        return (
            list(self._discoveries.values()) +
            list(self._questions.values()) +
            list(self._hypotheses.values()) +
            list(self._patterns.values())
        )

    def get_active(self, min_pull: float = 0.0) -> List[BaseCuriosity]:
        """
        Get all active curiosities sorted by pull (highest first).

        Active = not dormant/dissolved/answered status.
        """
        active = []

        # Check each type with its specific active statuses
        for discovery in self._discoveries.values():
            if discovery.status not in ["dormant"] and discovery.pull >= min_pull:
                active.append(discovery)

        for question in self._questions.values():
            if question.status not in ["dormant", "answered", "evolved"] and question.pull >= min_pull:
                active.append(question)

        for hypothesis in self._hypotheses.values():
            if hypothesis.status not in ["dormant", "confirmed", "refuted", "transformed"] and hypothesis.pull >= min_pull:
                active.append(hypothesis)

        for pattern in self._patterns.values():
            if pattern.status not in ["dissolved"] and pattern.pull >= min_pull:
                active.append(pattern)

        # Sort by pull (highest first)
        return sorted(active, key=lambda c: c.pull, reverse=True)

    def get_receptive(self) -> List[ReceptiveCuriosity]:
        """Get all receptive curiosities (Discovery, Question)."""
        return list(self._discoveries.values()) + list(self._questions.values())

    def get_assertive(self) -> List[AssertiveCuriosity]:
        """Get all assertive curiosities (Hypothesis, Pattern)."""
        return list(self._hypotheses.values()) + list(self._patterns.values())

    def get_hypotheses(self) -> List[Hypothesis]:
        """Get all hypotheses."""
        return list(self._hypotheses.values())

    def get_hypotheses_for_testing(self) -> List[Hypothesis]:
        """Get hypotheses that are actively being tested."""
        return [
            h for h in self._hypotheses.values()
            if h.status in ["weak", "testing", "supported"]
        ]

    def get_video_appropriate_hypotheses(self) -> List[Hypothesis]:
        """Get hypotheses that could be tested via video."""
        return [
            h for h in self._hypotheses.values()
            if h.video_appropriate and h.status in ["weak", "testing"]
        ]

    def get_patterns_by_domain(self, domain: str) -> List[Pattern]:
        """Get patterns involving a specific domain."""
        return [
            p for p in self._patterns.values()
            if domain in p.domains_involved
        ]

    def get_investigating(self) -> List[Hypothesis]:
        """
        Get hypotheses that have active investigations.

        Returns hypotheses where investigation is started and not stale.
        """
        return [
            h for h in self._hypotheses.values()
            if h.investigation and h.investigation.status == "active"
        ]

    def get_video_suggestable(self) -> List[Hypothesis]:
        """
        Get hypotheses that are appropriate for video suggestion.

        Returns hypotheses where video is appropriate but not yet requested.
        """
        return [
            h for h in self._hypotheses.values()
            if h.video_appropriate and not h.video_requested and h.status in ["weak", "testing"]
        ]

    # =========================================================================
    # Lineage Tracking
    # =========================================================================

    def get_lineage(self, curiosity_id: str) -> Optional[CuriosityLineage]:
        """
        Trace the evolution path of a curiosity.

        Returns lineage showing ancestors and descendants.
        """
        curiosity = self.get_by_id(curiosity_id)
        if not curiosity:
            return None

        ancestors = []
        descendants = []
        related_patterns = []

        # Find ancestors based on type
        if isinstance(curiosity, Question):
            if curiosity.source_discovery:
                ancestors.append(curiosity.source_discovery)
        elif isinstance(curiosity, Hypothesis):
            if curiosity.source_question:
                ancestors.append(curiosity.source_question)
            if curiosity.predecessor:
                ancestors.append(curiosity.predecessor)
        elif isinstance(curiosity, Pattern):
            ancestors.extend(curiosity.source_hypotheses)

        # Find descendants
        if isinstance(curiosity, Discovery):
            descendants.extend(curiosity.spawned_curiosities)
        elif isinstance(curiosity, Question):
            if curiosity.spawned_hypothesis:
                descendants.append(curiosity.spawned_hypothesis)
        elif isinstance(curiosity, Hypothesis):
            if curiosity.successor:
                descendants.append(curiosity.successor)
            related_patterns.extend(curiosity.contributed_to_patterns)

        return CuriosityLineage(
            curiosity_id=curiosity_id,
            curiosity_type=self._get_type_name(curiosity),
            focus=curiosity.focus,
            ancestors=ancestors,
            descendants=descendants,
            related_patterns=related_patterns,
        )

    def trace_full_lineage(self, curiosity_id: str) -> List[str]:
        """
        Trace the full lineage chain from root to this curiosity.

        Returns list of IDs from earliest ancestor to this curiosity.
        """
        chain = []
        visited = set()

        def trace_back(cid: str) -> None:
            if cid in visited:
                return
            visited.add(cid)

            lineage = self.get_lineage(cid)
            if lineage:
                for ancestor_id in lineage.ancestors:
                    trace_back(ancestor_id)
                chain.append(cid)

        trace_back(curiosity_id)
        return chain

    # =========================================================================
    # Updates
    # =========================================================================

    def update_curiosity(
        self,
        focus: str,
        new_fullness_or_confidence: Optional[float] = None,
        new_pull: Optional[float] = None,
        new_status: Optional[str] = None,
    ) -> Optional[BaseCuriosity]:
        """
        Update a curiosity by focus.

        Only updates specified fields (None = no change).
        Returns the updated curiosity or None if not found.
        """
        curiosity = self.get_by_focus(focus)
        if not curiosity:
            return None

        # Update fields
        if new_pull is not None:
            curiosity.pull = max(0.0, min(1.0, new_pull))

        if new_status is not None:
            curiosity.status = new_status

        if new_fullness_or_confidence is not None:
            value = max(0.0, min(1.0, new_fullness_or_confidence))
            if isinstance(curiosity, (Discovery, Question)):
                curiosity.fullness = value
            elif isinstance(curiosity, (Hypothesis, Pattern)):
                curiosity.confidence = value

        curiosity.last_updated = datetime.now()
        return curiosity

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize manager state to dictionary."""
        return {
            "discoveries": [d.to_dict() for d in self._discoveries.values()],
            "questions": [q.to_dict() for q in self._questions.values()],
            "hypotheses": [h.to_dict() for h in self._hypotheses.values()],
            "patterns": [p.to_dict() for p in self._patterns.values()],
            "baseline_video_requested": getattr(self, '_baseline_video_requested', False),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CuriosityManager":
        """Deserialize manager state from dictionary."""
        manager = cls()

        for d_data in data.get("discoveries", []):
            manager.add(Discovery.from_dict(d_data))

        for q_data in data.get("questions", []):
            manager.add(Question.from_dict(q_data))

        for h_data in data.get("hypotheses", []):
            manager.add(Hypothesis.from_dict(h_data))

        for p_data in data.get("patterns", []):
            manager.add(Pattern.from_dict(p_data))

        # Restore video flags
        if data.get("baseline_video_requested"):
            manager._baseline_video_requested = True

        return manager

    # =========================================================================
    # Stats
    # =========================================================================

    def get_counts(self) -> Dict[str, int]:
        """Get count of each curiosity type."""
        return {
            "discoveries": len(self._discoveries),
            "questions": len(self._questions),
            "hypotheses": len(self._hypotheses),
            "patterns": len(self._patterns),
            "total": (
                len(self._discoveries) +
                len(self._questions) +
                len(self._hypotheses) +
                len(self._patterns)
            ),
        }

    def get_domain_distribution(self) -> Dict[str, int]:
        """Get count of curiosities by domain."""
        distribution: Dict[str, int] = {}
        for curiosity in self.get_all():
            domain = curiosity.domain
            distribution[domain] = distribution.get(domain, 0) + 1
        return distribution

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_type_name(self, curiosity: BaseCuriosity) -> str:
        """Get the type name for a curiosity."""
        if isinstance(curiosity, Discovery):
            return "discovery"
        elif isinstance(curiosity, Question):
            return "question"
        elif isinstance(curiosity, Hypothesis):
            return "hypothesis"
        elif isinstance(curiosity, Pattern):
            return "pattern"
        return "unknown"

    def __iter__(self) -> Iterator[BaseCuriosity]:
        """Iterate over all curiosities."""
        yield from self._discoveries.values()
        yield from self._questions.values()
        yield from self._hypotheses.values()
        yield from self._patterns.values()

    def __len__(self) -> int:
        """Return total count of curiosities."""
        return (
            len(self._discoveries) +
            len(self._questions) +
            len(self._hypotheses) +
            len(self._patterns)
        )

    # =========================================================================
    # Gestalt Integration Methods
    # =========================================================================

    def get_gaps(self) -> List[BaseCuriosity]:
        """
        Get curiosities that represent gaps in understanding.

        Returns active curiosities with low fullness/confidence that
        are worth exploring further.
        """
        gaps = []
        threshold = 0.5  # Below this = gap in understanding

        for question in self._questions.values():
            if question.status in ["open", "partial"] and question.fullness < threshold:
                gaps.append(question)

        for hypothesis in self._hypotheses.values():
            if hypothesis.status in ["weak", "testing"] and hypothesis.confidence < threshold:
                gaps.append(hypothesis)

        # Sort by pull (highest first) - most pressing gaps first
        return sorted(gaps, key=lambda c: c.pull, reverse=True)

    def on_observation_learned(self, observation) -> None:
        """
        React to a new observation being learned.

        Boosts pull of curiosities related to the observation's domain.
        """
        domain = getattr(observation, 'domain', None)
        if domain:
            self.on_domain_touched(domain)

    def on_domain_touched(self, domain: str) -> None:
        """
        Boost curiosities related to a domain.

        Called when we learn something in a domain - related curiosities
        become more relevant.
        """
        boost_amount = 0.1

        for curiosity in self.get_all():
            if curiosity.domain == domain:
                curiosity.pull = min(1.0, curiosity.pull + boost_amount)
                curiosity.last_updated = datetime.now()

        # Also boost patterns that involve this domain
        for pattern in self._patterns.values():
            if domain in pattern.domains_involved:
                pattern.pull = min(1.0, pattern.pull + boost_amount * 0.5)
                pattern.last_updated = datetime.now()

    def on_evidence_added(self, focus: str, effect: str) -> None:
        """
        Update curiosity based on evidence effect.

        Args:
            focus: The curiosity focus
            effect: "supports", "contradicts", or "neutral"
        """
        curiosity = self.get_by_focus(focus)
        if not curiosity:
            return

        # Only assertive curiosities (Hypothesis, Pattern) have confidence
        if isinstance(curiosity, (Hypothesis, Pattern)):
            if effect == "supports":
                curiosity.confidence = min(1.0, curiosity.confidence + 0.1)
            elif effect == "contradicts":
                curiosity.confidence = max(0.0, curiosity.confidence - 0.15)
            # neutral doesn't change confidence

            curiosity.last_updated = datetime.now()

    def find_by_domains(self, domains: List[str]) -> Optional[Pattern]:
        """
        Find a pattern that involves the given domains.

        Returns the first pattern found that matches at least 2 of the domains.
        """
        if len(domains) < 2:
            return None

        domain_set = set(domains)
        for pattern in self._patterns.values():
            pattern_domains = set(pattern.domains_involved)
            # Match if at least 2 domains overlap
            if len(domain_set & pattern_domains) >= 2:
                return pattern

        return None

    def get_curiosity_by_investigation_id(self, investigation_id: str) -> Optional[Hypothesis]:
        """
        Find a hypothesis by its investigation ID.

        Used by video service to find the hypothesis being tested.
        """
        for hypothesis in self._hypotheses.values():
            if hypothesis.investigation and hypothesis.investigation.id == investigation_id:
                return hypothesis
        return None

    def mark_baseline_video_requested(self) -> None:
        """
        Mark that baseline video has been requested.

        Stored as a flag in the manager state to prevent re-suggesting.
        """
        self._baseline_video_requested = True

    @property
    def baseline_video_requested(self) -> bool:
        """Check if baseline video has been requested."""
        return getattr(self, '_baseline_video_requested', False)

    def should_suggest_baseline_video(self, message_count: int) -> bool:
        """
        Check if baseline video should be suggested.

        Suggests between messages 3-15 if not already requested.
        """
        if self.baseline_video_requested:
            return False
        # Suggest between messages 3-15
        return 3 <= message_count <= 15

    # Alias for backwards compatibility with video_service
    def add_curiosity(self, curiosity: BaseCuriosity) -> None:
        """Alias for add() - for compatibility."""
        self.add(curiosity)
