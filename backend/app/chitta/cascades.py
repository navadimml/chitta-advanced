"""
Cascade Handler - Handling Ripple Effects of Curiosity Changes

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module handles cascading effects when significant curiosity changes occur.
For example, when a hypothesis is refuted:
1. The source question should be reopened
2. Connected patterns should be weakened
3. The crystal should be marked for regeneration

Cascades create a chain of events that must all be recorded.

CASCADES ARE TRIGGERED BY:
- Hypothesis refutation → reopen question, weaken patterns
- Hypothesis confirmation → strengthen patterns, potentially create new ones
- Pattern dissolution → update source hypotheses
- Evidence contradicting high-confidence beliefs

CASCADES ARE NOT:
- Regular updates (those are direct)
- Decay (that's mechanical)
- New curiosity creation (that's direct from LLM)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .curiosity_types import (
    BaseCuriosity,
    Discovery,
    Question,
    Hypothesis,
    Pattern,
)
from .curiosity_manager import CuriosityManager
from .events import (
    CuriosityEvent,
    Change,
    CURIOSITY_UPDATED,
    CURIOSITY_REFUTED,
    PATTERN_QUESTIONED,
    PATTERN_DISSOLVED,
    PATTERN_STRENGTHENED,
    ENTITY_CURIOSITY,
    ENTITY_PATTERN,
)


@dataclass
class CascadeResult:
    """Result of a cascade operation."""
    affected_curiosities: List[str]  # IDs of curiosities that changed
    events: List[CuriosityEvent]  # Events generated
    crystal_needs_regeneration: bool


class CascadeHandler:
    """
    Handles cascading effects of curiosity changes.

    When a significant change occurs (refutation, dissolution), related
    curiosities may need to be updated. This handler determines what
    changes are needed and creates the corresponding events.
    """

    def __init__(self, manager: CuriosityManager):
        """Initialize with curiosity manager."""
        self._manager = manager

    def handle_refutation(
        self,
        hypothesis: Hypothesis,
        session_id: str,
        child_id: str,
        refutation_reasoning: str,
    ) -> CascadeResult:
        """
        Handle cascade effects when a hypothesis is refuted.

        Effects:
        1. Reopen source question (if exists)
        2. Weaken patterns that relied on this hypothesis
        3. Mark crystal for regeneration

        Returns cascade result with all generated events.
        """
        events = []
        affected = []

        # 1. Reopen source question
        if hypothesis.source_question:
            question = self._manager.get_by_focus(hypothesis.source_question)
            if question and isinstance(question, Question):
                # Question goes back to open/partial
                old_status = question.status
                question.status = "partial" if question.fullness > 0.3 else "open"
                question.spawned_hypothesis = None  # Clear the link
                question.last_updated = datetime.now()

                event = CuriosityEvent.create(
                    event_type=CURIOSITY_UPDATED,
                    entity_type=ENTITY_CURIOSITY,
                    entity_id=question.id,
                    changes={
                        "status": Change("status", old_status, question.status),
                        "spawned_hypothesis": Change("spawned_hypothesis", hypothesis.focus, None),
                    },
                    reasoning=f"Source hypothesis '{hypothesis.focus}' was refuted: {refutation_reasoning}",
                    evidence_refs=[],
                    session_id=session_id,
                    child_id=child_id,
                    triggered_by=hypothesis.id,
                )
                events.append(event)
                affected.append(question.id)

        # 2. Weaken patterns that relied on this hypothesis
        for pattern_focus in hypothesis.contributed_to_patterns:
            pattern = self._manager.get_by_focus(pattern_focus)
            if pattern and isinstance(pattern, Pattern):
                # Reduce pattern confidence
                old_confidence = pattern.confidence
                # Weaken by 30% - significant but not fatal
                new_confidence = max(0.1, old_confidence * 0.7)
                pattern.confidence = new_confidence
                pattern.last_updated = datetime.now()

                # If confidence drops too low, pattern becomes questioned
                old_status = pattern.status
                if new_confidence < 0.3 and pattern.status == "solid":
                    pattern.status = "questioned"

                event = CuriosityEvent.create(
                    event_type=PATTERN_QUESTIONED if pattern.status == "questioned" else CURIOSITY_UPDATED,
                    entity_type=ENTITY_PATTERN,
                    entity_id=pattern.id,
                    changes={
                        "confidence": Change("confidence", old_confidence, new_confidence),
                        "status": Change("status", old_status, pattern.status),
                    },
                    reasoning=f"Source hypothesis '{hypothesis.focus}' was refuted: {refutation_reasoning}",
                    evidence_refs=[],
                    session_id=session_id,
                    child_id=child_id,
                    triggered_by=hypothesis.id,
                )
                events.append(event)
                affected.append(pattern.id)

        # Crystal always needs regeneration after refutation
        return CascadeResult(
            affected_curiosities=affected,
            events=events,
            crystal_needs_regeneration=True,
        )

    def handle_confirmation(
        self,
        hypothesis: Hypothesis,
        session_id: str,
        child_id: str,
        confirmation_reasoning: str,
    ) -> CascadeResult:
        """
        Handle cascade effects when a hypothesis is confirmed.

        Effects:
        1. Mark source question as answered (if exists)
        2. Strengthen patterns that include this hypothesis
        3. Mark crystal for regeneration (new confident knowledge)

        Returns cascade result with all generated events.
        """
        events = []
        affected = []

        # 1. Mark source question as answered
        if hypothesis.source_question:
            question = self._manager.get_by_focus(hypothesis.source_question)
            if question and isinstance(question, Question):
                old_status = question.status
                question.status = "answered"
                question.fullness = 1.0  # Fully answered
                question.last_updated = datetime.now()

                event = CuriosityEvent.create(
                    event_type=CURIOSITY_UPDATED,
                    entity_type=ENTITY_CURIOSITY,
                    entity_id=question.id,
                    changes={
                        "status": Change("status", old_status, "answered"),
                        "fullness": Change("fullness", question.fullness, 1.0),
                    },
                    reasoning=f"Hypothesis '{hypothesis.focus}' was confirmed: {confirmation_reasoning}",
                    evidence_refs=[],
                    session_id=session_id,
                    child_id=child_id,
                    triggered_by=hypothesis.id,
                )
                events.append(event)
                affected.append(question.id)

        # 2. Strengthen patterns that include this hypothesis
        for pattern_focus in hypothesis.contributed_to_patterns:
            pattern = self._manager.get_by_focus(pattern_focus)
            if pattern and isinstance(pattern, Pattern):
                old_confidence = pattern.confidence
                # Strengthen by 20% (capped at 1.0)
                new_confidence = min(1.0, old_confidence * 1.2)
                pattern.confidence = new_confidence
                pattern.last_updated = datetime.now()

                # Pattern might become solid/foundational
                old_status = pattern.status
                if new_confidence >= 0.8 and pattern.status == "solid":
                    pattern.status = "foundational"
                elif new_confidence >= 0.5 and pattern.status == "emerging":
                    pattern.status = "solid"

                event = CuriosityEvent.create(
                    event_type=PATTERN_STRENGTHENED,
                    entity_type=ENTITY_PATTERN,
                    entity_id=pattern.id,
                    changes={
                        "confidence": Change("confidence", old_confidence, new_confidence),
                        "status": Change("status", old_status, pattern.status),
                    },
                    reasoning=f"Source hypothesis '{hypothesis.focus}' was confirmed: {confirmation_reasoning}",
                    evidence_refs=[],
                    session_id=session_id,
                    child_id=child_id,
                    triggered_by=hypothesis.id,
                )
                events.append(event)
                affected.append(pattern.id)

        # Crystal needs regeneration for new confident knowledge
        return CascadeResult(
            affected_curiosities=affected,
            events=events,
            crystal_needs_regeneration=True,
        )

    def handle_pattern_dissolved(
        self,
        pattern: Pattern,
        session_id: str,
        child_id: str,
        dissolution_reasoning: str,
    ) -> CascadeResult:
        """
        Handle cascade effects when a pattern is dissolved.

        Effects:
        1. Update source hypotheses (remove pattern from their contributed_to_patterns)
        2. Reopen any questions that were spawned by this pattern
        3. Mark crystal for regeneration

        Returns cascade result with all generated events.
        """
        events = []
        affected = []

        # 1. Update source hypotheses
        for hyp_focus in pattern.source_hypotheses:
            hypothesis = self._manager.get_by_focus(hyp_focus)
            if hypothesis and isinstance(hypothesis, Hypothesis):
                # Remove pattern from contributed_to_patterns
                if pattern.focus in hypothesis.contributed_to_patterns:
                    hypothesis.contributed_to_patterns.remove(pattern.focus)
                    hypothesis.last_updated = datetime.now()

                    event = CuriosityEvent.create(
                        event_type=CURIOSITY_UPDATED,
                        entity_type=ENTITY_CURIOSITY,
                        entity_id=hypothesis.id,
                        changes={
                            "contributed_to_patterns": Change(
                                "contributed_to_patterns",
                                hypothesis.contributed_to_patterns + [pattern.focus],
                                hypothesis.contributed_to_patterns,
                            ),
                        },
                        reasoning=f"Pattern '{pattern.focus}' was dissolved: {dissolution_reasoning}",
                        evidence_refs=[],
                        session_id=session_id,
                        child_id=child_id,
                        triggered_by=pattern.id,
                    )
                    events.append(event)
                    affected.append(hypothesis.id)

        # 2. Reopen spawned questions
        for q_focus in pattern.spawned_questions:
            question = self._manager.get_by_focus(q_focus)
            if question and isinstance(question, Question):
                old_status = question.status
                if question.status != "answered":  # Don't reopen answered questions
                    question.status = "open"
                    question.last_updated = datetime.now()

                    event = CuriosityEvent.create(
                        event_type=CURIOSITY_UPDATED,
                        entity_type=ENTITY_CURIOSITY,
                        entity_id=question.id,
                        changes={
                            "status": Change("status", old_status, "open"),
                        },
                        reasoning=f"Source pattern '{pattern.focus}' was dissolved: {dissolution_reasoning}",
                        evidence_refs=[],
                        session_id=session_id,
                        child_id=child_id,
                        triggered_by=pattern.id,
                    )
                    events.append(event)
                    affected.append(question.id)

        # Crystal needs regeneration
        return CascadeResult(
            affected_curiosities=affected,
            events=events,
            crystal_needs_regeneration=True,
        )

    def handle_evidence_contradiction(
        self,
        curiosity: BaseCuriosity,
        old_confidence: float,
        new_confidence: float,
        session_id: str,
        child_id: str,
        contradiction_reasoning: str,
    ) -> CascadeResult:
        """
        Handle cascade effects when evidence significantly contradicts a belief.

        This is called when evidence drops confidence significantly (>30% drop).

        Effects depend on the curiosity type and how much confidence dropped.
        """
        events = []
        affected = []
        crystal_needs_regen = False

        # Only applies to assertive curiosities
        if not isinstance(curiosity, (Hypothesis, Pattern)):
            return CascadeResult(
                affected_curiosities=[],
                events=[],
                crystal_needs_regeneration=False,
            )

        confidence_drop = old_confidence - new_confidence

        # Significant contradiction (>40% drop from high confidence)
        if confidence_drop > 0.4 and old_confidence >= 0.7:
            # This is a major shift in understanding
            crystal_needs_regen = True

            # If it's a hypothesis with connected patterns, weaken them
            if isinstance(curiosity, Hypothesis):
                for pattern_focus in curiosity.contributed_to_patterns:
                    pattern = self._manager.get_by_focus(pattern_focus)
                    if pattern and isinstance(pattern, Pattern):
                        # Reduce pattern confidence proportionally
                        old_p_conf = pattern.confidence
                        reduction = min(0.2, confidence_drop * 0.3)
                        new_p_conf = max(0.1, old_p_conf - reduction)
                        pattern.confidence = new_p_conf
                        pattern.last_updated = datetime.now()

                        event = CuriosityEvent.create(
                            event_type=CURIOSITY_UPDATED,
                            entity_type=ENTITY_PATTERN,
                            entity_id=pattern.id,
                            changes={
                                "confidence": Change("confidence", old_p_conf, new_p_conf),
                            },
                            reasoning=f"Source hypothesis '{curiosity.focus}' significantly weakened: {contradiction_reasoning}",
                            evidence_refs=[],
                            session_id=session_id,
                            child_id=child_id,
                            triggered_by=curiosity.id,
                        )
                        events.append(event)
                        affected.append(pattern.id)

        return CascadeResult(
            affected_curiosities=affected,
            events=events,
            crystal_needs_regeneration=crystal_needs_regen,
        )
