"""
Event Recorder - High-Level Service for Recording Events

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module provides a high-level interface for recording events.
It handles cascade tracking and batch commits.

RESPONSIBILITIES:
- Record events with proper provenance
- Track cascade relationships
- Batch multiple events in a transaction
- Validate reasoning requirements

USAGE:
    recorder = EventRecorder(event_store, session_id, child_id)

    # Record single event
    event = await recorder.record_observation_added(...)

    # Record with cascade
    async with recorder.cascade(parent_event) as cascade:
        cascade.record_curiosity_updated(...)
        cascade.record_pattern_questioned(...)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from .events import (
    CuriosityEvent,
    Change,
    build_observation_added_event,
    build_curiosity_created_event,
    build_curiosity_updated_event,
    build_evidence_added_event,
    build_curiosity_evolved_event,
    build_curiosity_refuted_event,
    build_pattern_emerged_event,
    build_crystal_synthesized_event,
    CURIOSITY_UPDATED,
    CURIOSITY_DORMANT,
    CURIOSITY_REVIVED,
    PATTERN_QUESTIONED,
    PATTERN_DISSOLVED,
    PATTERN_STRENGTHENED,
    ENTITY_CURIOSITY,
    ENTITY_PATTERN,
)
from .event_store import EventStore


class EventRecorder:
    """
    High-level service for recording curiosity events.

    Provides convenience methods for common event types and
    handles cascade tracking automatically.
    """

    def __init__(
        self,
        event_store: EventStore,
        session_id: str,
        child_id: str,
    ):
        """
        Initialize recorder for a session.

        Args:
            event_store: The event store to write to
            session_id: Current session ID
            child_id: Child ID for all events
        """
        self._store = event_store
        self._session_id = session_id
        self._child_id = child_id
        self._pending_events: List[CuriosityEvent] = []

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def child_id(self) -> str:
        return self._child_id

    async def flush(self) -> List[CuriosityEvent]:
        """
        Write all pending events to the store.

        Returns the list of events that were written.
        """
        if not self._pending_events:
            return []

        events = self._pending_events.copy()
        await self._store.append_batch(events)
        self._pending_events.clear()
        return events

    def queue(self, event: CuriosityEvent) -> CuriosityEvent:
        """
        Queue an event for later writing.

        Use flush() to write all queued events.
        """
        self._pending_events.append(event)
        return event

    async def record(self, event: CuriosityEvent) -> CuriosityEvent:
        """
        Record an event immediately.

        For immediate writes. Use queue() + flush() for batching.
        """
        await self._store.append(event)
        return event

    # =========================================================================
    # Observation Events
    # =========================================================================

    async def record_observation_added(
        self,
        observation_id: str,
        content: str,
        domain: str,
        addresses_curiosity: Optional[str] = None,
    ) -> CuriosityEvent:
        """Record an observation added event."""
        event = build_observation_added_event(
            observation_id=observation_id,
            content=content,
            domain=domain,
            session_id=self._session_id,
            child_id=self._child_id,
            addresses_curiosity=addresses_curiosity,
        )
        return await self.record(event)

    # =========================================================================
    # Curiosity Lifecycle Events
    # =========================================================================

    async def record_curiosity_created(
        self,
        curiosity_id: str,
        curiosity_type: str,
        focus: str,
        domain: str,
        initial_value: float,
        reasoning: str,
        evidence_refs: List[str],
        emerges_from: Optional[str] = None,
    ) -> CuriosityEvent:
        """Record a curiosity created event."""
        event = build_curiosity_created_event(
            curiosity_id=curiosity_id,
            curiosity_type=curiosity_type,
            focus=focus,
            domain=domain,
            initial_value=initial_value,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            session_id=self._session_id,
            child_id=self._child_id,
            emerges_from=emerges_from,
        )
        return await self.record(event)

    async def record_curiosity_updated(
        self,
        curiosity_id: str,
        changes: Dict[str, Change],
        reasoning: str,
        evidence_refs: List[str],
        triggered_by: Optional[str] = None,
    ) -> CuriosityEvent:
        """Record a curiosity updated event."""
        event = build_curiosity_updated_event(
            curiosity_id=curiosity_id,
            changes=changes,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            session_id=self._session_id,
            child_id=self._child_id,
            triggered_by=triggered_by,
        )
        return await self.record(event)

    async def record_curiosity_evolved(
        self,
        source_curiosity_id: str,
        target_curiosity_id: str,
        reasoning: str,
        evidence_refs: List[str],
    ) -> CuriosityEvent:
        """Record a curiosity evolved event (Question → Hypothesis)."""
        event = build_curiosity_evolved_event(
            source_curiosity_id=source_curiosity_id,
            target_curiosity_id=target_curiosity_id,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            session_id=self._session_id,
            child_id=self._child_id,
        )
        return await self.record(event)

    async def record_curiosity_refuted(
        self,
        curiosity_id: str,
        reasoning: str,
        evidence_refs: List[str],
        triggered_by: Optional[str] = None,
    ) -> CuriosityEvent:
        """Record a curiosity refuted event."""
        event = build_curiosity_refuted_event(
            curiosity_id=curiosity_id,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            session_id=self._session_id,
            child_id=self._child_id,
            triggered_by=triggered_by,
        )
        return await self.record(event)

    async def record_curiosity_dormant(
        self,
        curiosity_id: str,
        reasoning: str,
    ) -> CuriosityEvent:
        """Record a curiosity becoming dormant."""
        event = CuriosityEvent.create(
            event_type=CURIOSITY_DORMANT,
            entity_type=ENTITY_CURIOSITY,
            entity_id=curiosity_id,
            changes={"status": Change("status", "active", "dormant")},
            reasoning=reasoning,
            evidence_refs=[],
            session_id=self._session_id,
            child_id=self._child_id,
        )
        return await self.record(event)

    async def record_curiosity_revived(
        self,
        curiosity_id: str,
        reasoning: str,
        evidence_refs: List[str],
    ) -> CuriosityEvent:
        """Record a dormant curiosity being revived."""
        event = CuriosityEvent.create(
            event_type=CURIOSITY_REVIVED,
            entity_type=ENTITY_CURIOSITY,
            entity_id=curiosity_id,
            changes={"status": Change("status", "dormant", "active")},
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            session_id=self._session_id,
            child_id=self._child_id,
        )
        return await self.record(event)

    # =========================================================================
    # Evidence Events
    # =========================================================================

    async def record_evidence_added(
        self,
        evidence_id: str,
        curiosity_id: str,
        content: str,
        effect: str,
        confidence_before: float,
        confidence_after: float,
        reasoning: str,
        source_observation: str,
    ) -> CuriosityEvent:
        """Record an evidence added event."""
        event = build_evidence_added_event(
            evidence_id=evidence_id,
            curiosity_id=curiosity_id,
            content=content,
            effect=effect,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            reasoning=reasoning,
            source_observation=source_observation,
            session_id=self._session_id,
            child_id=self._child_id,
        )
        return await self.record(event)

    # =========================================================================
    # Pattern Events
    # =========================================================================

    async def record_pattern_emerged(
        self,
        pattern_id: str,
        focus: str,
        insight: str,
        domains_involved: List[str],
        source_hypotheses: List[str],
        confidence: float,
        reasoning: str,
    ) -> CuriosityEvent:
        """Record a pattern emerged event."""
        event = build_pattern_emerged_event(
            pattern_id=pattern_id,
            focus=focus,
            insight=insight,
            domains_involved=domains_involved,
            source_hypotheses=source_hypotheses,
            confidence=confidence,
            reasoning=reasoning,
            session_id=self._session_id,
            child_id=self._child_id,
        )
        return await self.record(event)

    async def record_pattern_strengthened(
        self,
        pattern_id: str,
        old_confidence: float,
        new_confidence: float,
        reasoning: str,
        evidence_refs: List[str],
        triggered_by: Optional[str] = None,
    ) -> CuriosityEvent:
        """Record a pattern being strengthened."""
        event = CuriosityEvent.create(
            event_type=PATTERN_STRENGTHENED,
            entity_type=ENTITY_PATTERN,
            entity_id=pattern_id,
            changes={"confidence": Change("confidence", old_confidence, new_confidence)},
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            session_id=self._session_id,
            child_id=self._child_id,
            triggered_by=triggered_by,
        )
        return await self.record(event)

    async def record_pattern_questioned(
        self,
        pattern_id: str,
        old_confidence: float,
        new_confidence: float,
        reasoning: str,
        triggered_by: Optional[str] = None,
    ) -> CuriosityEvent:
        """Record a pattern being questioned."""
        event = CuriosityEvent.create(
            event_type=PATTERN_QUESTIONED,
            entity_type=ENTITY_PATTERN,
            entity_id=pattern_id,
            changes={
                "status": Change("status", "solid", "questioned"),
                "confidence": Change("confidence", old_confidence, new_confidence),
            },
            reasoning=reasoning,
            evidence_refs=[],
            session_id=self._session_id,
            child_id=self._child_id,
            triggered_by=triggered_by,
        )
        return await self.record(event)

    async def record_pattern_dissolved(
        self,
        pattern_id: str,
        reasoning: str,
        triggered_by: Optional[str] = None,
    ) -> CuriosityEvent:
        """Record a pattern being dissolved."""
        event = CuriosityEvent.create(
            event_type=PATTERN_DISSOLVED,
            entity_type=ENTITY_PATTERN,
            entity_id=pattern_id,
            changes={"status": Change("status", "questioned", "dissolved")},
            reasoning=reasoning,
            evidence_refs=[],
            session_id=self._session_id,
            child_id=self._child_id,
            triggered_by=triggered_by,
        )
        return await self.record(event)

    # =========================================================================
    # Crystal Events
    # =========================================================================

    async def record_crystal_synthesized(
        self,
        crystal_version: int,
        source_observations: List[str],
        source_patterns: List[str],
        reasoning: str,
    ) -> CuriosityEvent:
        """Record a crystal synthesized event."""
        event = build_crystal_synthesized_event(
            crystal_version=crystal_version,
            source_observations=source_observations,
            source_patterns=source_patterns,
            reasoning=reasoning,
            session_id=self._session_id,
            child_id=self._child_id,
        )
        return await self.record(event)

    # =========================================================================
    # Cascade Context Manager
    # =========================================================================

    @asynccontextmanager
    async def cascade(self, parent_event: CuriosityEvent):
        """
        Context manager for recording cascaded events.

        All events recorded within this context will have their
        triggered_by set to the parent event, and the parent will
        have its triggered_events updated.

        Usage:
            parent = await recorder.record_curiosity_refuted(...)
            async with recorder.cascade(parent) as cascade:
                await cascade.record_pattern_questioned(...)
                await cascade.record_curiosity_updated(...)
        """
        cascade_recorder = CascadeRecorder(
            self,
            parent_event,
        )
        yield cascade_recorder

        # Update parent with triggered events
        if cascade_recorder._triggered_events:
            parent_event.triggered_events.extend(cascade_recorder._triggered_events)


class CascadeRecorder:
    """
    Helper for recording cascaded events.

    All events recorded through this recorder will be linked
    to the parent event via triggered_by.
    """

    def __init__(
        self,
        parent_recorder: EventRecorder,
        parent_event: CuriosityEvent,
    ):
        self._parent = parent_recorder
        self._parent_event = parent_event
        self._triggered_events: List[str] = []

    async def record_curiosity_updated(
        self,
        curiosity_id: str,
        changes: Dict[str, Change],
        reasoning: str,
        evidence_refs: List[str],
    ) -> CuriosityEvent:
        """Record a cascaded curiosity update."""
        event = await self._parent.record_curiosity_updated(
            curiosity_id=curiosity_id,
            changes=changes,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            triggered_by=self._parent_event.id,
        )
        self._triggered_events.append(event.id)
        return event

    async def record_curiosity_refuted(
        self,
        curiosity_id: str,
        reasoning: str,
        evidence_refs: List[str],
    ) -> CuriosityEvent:
        """Record a cascaded curiosity refutation."""
        event = await self._parent.record_curiosity_refuted(
            curiosity_id=curiosity_id,
            reasoning=reasoning,
            evidence_refs=evidence_refs,
            triggered_by=self._parent_event.id,
        )
        self._triggered_events.append(event.id)
        return event

    async def record_pattern_questioned(
        self,
        pattern_id: str,
        old_confidence: float,
        new_confidence: float,
        reasoning: str,
    ) -> CuriosityEvent:
        """Record a cascaded pattern questioning."""
        event = await self._parent.record_pattern_questioned(
            pattern_id=pattern_id,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            reasoning=reasoning,
            triggered_by=self._parent_event.id,
        )
        self._triggered_events.append(event.id)
        return event

    async def record_pattern_dissolved(
        self,
        pattern_id: str,
        reasoning: str,
    ) -> CuriosityEvent:
        """Record a cascaded pattern dissolution."""
        event = await self._parent.record_pattern_dissolved(
            pattern_id=pattern_id,
            reasoning=reasoning,
            triggered_by=self._parent_event.id,
        )
        self._triggered_events.append(event.id)
        return event
