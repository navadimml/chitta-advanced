"""
Event Store - Persistence and Query for Curiosity Events

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module provides the event store interface and implementations.
The store is append-only - events are immutable once written.

CAPABILITIES:
- Append events
- Query by entity, session, time range, child
- Reconstruct entity state at any point in time
- Get cascade chains (triggered_by relationships)

IMPLEMENTATIONS:
- InMemoryEventStore: For testing and development
- DatabaseEventStore: For production (uses SQLAlchemy)
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from collections import defaultdict

from .events import CuriosityEvent, Change


class EventStore(ABC):
    """
    Abstract interface for event storage.

    All implementations must be append-only and support
    the full query interface for explainability.
    """

    @abstractmethod
    async def append(self, event: CuriosityEvent) -> None:
        """
        Store an event.

        Events are immutable once stored.
        """
        pass

    @abstractmethod
    async def append_batch(self, events: List[CuriosityEvent]) -> None:
        """
        Store multiple events atomically.

        Used for cascades where multiple events happen together.
        """
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[CuriosityEvent]:
        """Get a single event by ID."""
        pass

    @abstractmethod
    async def get_events_for_entity(self, entity_id: str) -> List[CuriosityEvent]:
        """
        Get all events for an entity.

        Returns events in chronological order.
        """
        pass

    @abstractmethod
    async def get_events_for_child(
        self,
        child_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[CuriosityEvent]:
        """
        Get all events for a child.

        Returns events in reverse chronological order (newest first).
        """
        pass

    @abstractmethod
    async def get_events_in_session(self, session_id: str) -> List[CuriosityEvent]:
        """
        Get all events in a session.

        Returns events in chronological order.
        """
        pass

    @abstractmethod
    async def get_events_between(
        self,
        child_id: str,
        start: datetime,
        end: datetime,
    ) -> List[CuriosityEvent]:
        """
        Get events in a time range for a child.

        Returns events in chronological order.
        """
        pass

    @abstractmethod
    async def get_events_by_type(
        self,
        child_id: str,
        event_type: str,
        limit: Optional[int] = None,
    ) -> List[CuriosityEvent]:
        """Get events of a specific type for a child."""
        pass

    @abstractmethod
    async def get_cascade_chain(self, event_id: str) -> List[CuriosityEvent]:
        """
        Get the full cascade chain starting from an event.

        Returns the event and all events it triggered (recursively).
        """
        pass

    @abstractmethod
    async def get_event_count(self, child_id: str) -> int:
        """Get total event count for a child."""
        pass

    async def reconstruct_entity_at(
        self,
        entity_id: str,
        timestamp: datetime,
    ) -> Dict[str, Any]:
        """
        Reconstruct entity state at a specific point in time.

        Replays all events up to the timestamp to build state.
        """
        events = await self.get_events_for_entity(entity_id)

        # Filter to events before timestamp
        relevant_events = [e for e in events if e.timestamp <= timestamp]

        # Build state by applying changes
        state: Dict[str, Any] = {"entity_id": entity_id}
        for event in relevant_events:
            for field_name, change in event.changes.items():
                state[field_name] = change.to_value

        return state


class InMemoryEventStore(EventStore):
    """
    In-memory event store for testing and development.

    NOT for production - events are lost on restart.
    """

    def __init__(self):
        self._events: Dict[str, CuriosityEvent] = {}  # event_id -> event
        self._by_entity: Dict[str, List[str]] = defaultdict(list)  # entity_id -> [event_ids]
        self._by_child: Dict[str, List[str]] = defaultdict(list)  # child_id -> [event_ids]
        self._by_session: Dict[str, List[str]] = defaultdict(list)  # session_id -> [event_ids]

    async def append(self, event: CuriosityEvent) -> None:
        """Store an event."""
        self._events[event.id] = event
        self._by_entity[event.entity_id].append(event.id)
        self._by_child[event.child_id].append(event.id)
        self._by_session[event.session_id].append(event.id)

    async def append_batch(self, events: List[CuriosityEvent]) -> None:
        """Store multiple events."""
        for event in events:
            await self.append(event)

    async def get_event(self, event_id: str) -> Optional[CuriosityEvent]:
        """Get a single event by ID."""
        return self._events.get(event_id)

    async def get_events_for_entity(self, entity_id: str) -> List[CuriosityEvent]:
        """Get all events for an entity in chronological order."""
        event_ids = self._by_entity.get(entity_id, [])
        events = [self._events[eid] for eid in event_ids if eid in self._events]
        return sorted(events, key=lambda e: e.timestamp)

    async def get_events_for_child(
        self,
        child_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[CuriosityEvent]:
        """Get events for a child in reverse chronological order."""
        event_ids = self._by_child.get(child_id, [])
        events = [self._events[eid] for eid in event_ids if eid in self._events]
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        # Apply offset and limit
        if offset:
            events = events[offset:]
        if limit:
            events = events[:limit]

        return events

    async def get_events_in_session(self, session_id: str) -> List[CuriosityEvent]:
        """Get events in a session in chronological order."""
        event_ids = self._by_session.get(session_id, [])
        events = [self._events[eid] for eid in event_ids if eid in self._events]
        return sorted(events, key=lambda e: e.timestamp)

    async def get_events_between(
        self,
        child_id: str,
        start: datetime,
        end: datetime,
    ) -> List[CuriosityEvent]:
        """Get events in a time range."""
        event_ids = self._by_child.get(child_id, [])
        events = [self._events[eid] for eid in event_ids if eid in self._events]
        filtered = [e for e in events if start <= e.timestamp <= end]
        return sorted(filtered, key=lambda e: e.timestamp)

    async def get_events_by_type(
        self,
        child_id: str,
        event_type: str,
        limit: Optional[int] = None,
    ) -> List[CuriosityEvent]:
        """Get events of a specific type."""
        event_ids = self._by_child.get(child_id, [])
        events = [self._events[eid] for eid in event_ids if eid in self._events]
        filtered = [e for e in events if e.event_type == event_type]
        filtered = sorted(filtered, key=lambda e: e.timestamp, reverse=True)
        if limit:
            filtered = filtered[:limit]
        return filtered

    async def get_cascade_chain(self, event_id: str) -> List[CuriosityEvent]:
        """Get cascade chain recursively."""
        result = []
        event = await self.get_event(event_id)
        if not event:
            return result

        result.append(event)
        for triggered_id in event.triggered_events:
            result.extend(await self.get_cascade_chain(triggered_id))

        return result

    async def get_event_count(self, child_id: str) -> int:
        """Get event count for a child."""
        return len(self._by_child.get(child_id, []))

    def clear(self):
        """Clear all events (for testing)."""
        self._events.clear()
        self._by_entity.clear()
        self._by_child.clear()
        self._by_session.clear()


# =============================================================================
# Database Event Store (Production)
# =============================================================================

class DatabaseEventStore(EventStore):
    """
    Database-backed event store for production.

    Uses SQLAlchemy async session for persistence.
    Events are stored in the curiosity_events table.
    """

    def __init__(self, session_factory):
        """
        Initialize with async session factory.

        Args:
            session_factory: Callable that returns an async session context manager
        """
        self._session_factory = session_factory

    async def append(self, event: CuriosityEvent) -> None:
        """Store an event in the database."""
        from app.db.models_events import CuriosityEventDB
        import json

        async with self._session_factory() as session:
            db_event = CuriosityEventDB(
                id=event.id,
                timestamp=event.timestamp,
                session_id=event.session_id,
                child_id=event.child_id,
                event_type=event.event_type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                changes_json=json.dumps({k: v.to_dict() for k, v in event.changes.items()}, ensure_ascii=False),
                reasoning=event.reasoning,
                evidence_refs_json=json.dumps(event.evidence_refs, ensure_ascii=False),
                triggered_by=event.triggered_by,
            )
            session.add(db_event)
            await session.commit()

    async def append_batch(self, events: List[CuriosityEvent]) -> None:
        """Store multiple events atomically."""
        from app.db.models_events import CuriosityEventDB
        import json

        async with self._session_factory() as session:
            for event in events:
                db_event = CuriosityEventDB(
                    id=event.id,
                    timestamp=event.timestamp,
                    session_id=event.session_id,
                    child_id=event.child_id,
                    event_type=event.event_type,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    changes_json=json.dumps({k: v.to_dict() for k, v in event.changes.items()}, ensure_ascii=False),
                    reasoning=event.reasoning,
                    evidence_refs_json=json.dumps(event.evidence_refs, ensure_ascii=False),
                    triggered_by=event.triggered_by,
                )
                session.add(db_event)
            await session.commit()

    def _db_to_event(self, db_event) -> CuriosityEvent:
        """Convert database model to event."""
        import json
        from .events import Change

        changes_data = json.loads(db_event.changes_json) if db_event.changes_json else {}
        changes = {k: Change.from_dict(v) for k, v in changes_data.items()}

        evidence_refs = json.loads(db_event.evidence_refs_json) if db_event.evidence_refs_json else []

        return CuriosityEvent(
            id=db_event.id,
            timestamp=db_event.timestamp,
            session_id=db_event.session_id,
            child_id=str(db_event.child_id),
            event_type=db_event.event_type,
            entity_type=db_event.entity_type,
            entity_id=db_event.entity_id,
            changes=changes,
            reasoning=db_event.reasoning or "",
            evidence_refs=evidence_refs,
            triggered_by=db_event.triggered_by,
            triggered_events=[],  # TODO: Load from triggered events if needed
        )

    async def get_event(self, event_id: str) -> Optional[CuriosityEvent]:
        """Get a single event by ID."""
        from sqlalchemy import select
        from app.db.models_events import CuriosityEventDB

        async with self._session_factory() as session:
            result = await session.execute(
                select(CuriosityEventDB).where(CuriosityEventDB.id == event_id)
            )
            db_event = result.scalar_one_or_none()
            if db_event:
                return self._db_to_event(db_event)
            return None

    async def get_events_for_entity(self, entity_id: str) -> List[CuriosityEvent]:
        """Get all events for an entity."""
        from sqlalchemy import select
        from app.db.models_events import CuriosityEventDB

        async with self._session_factory() as session:
            result = await session.execute(
                select(CuriosityEventDB)
                .where(CuriosityEventDB.entity_id == entity_id)
                .order_by(CuriosityEventDB.timestamp)
            )
            return [self._db_to_event(e) for e in result.scalars()]

    async def get_events_for_child(
        self,
        child_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[CuriosityEvent]:
        """Get events for a child."""
        from sqlalchemy import select
        from app.db.models_events import CuriosityEventDB

        async with self._session_factory() as session:
            query = (
                select(CuriosityEventDB)
                .where(CuriosityEventDB.child_id == child_id)
                .order_by(CuriosityEventDB.timestamp.desc())
                .offset(offset)
            )
            if limit:
                query = query.limit(limit)

            result = await session.execute(query)
            return [self._db_to_event(e) for e in result.scalars()]

    async def get_events_in_session(self, session_id: str) -> List[CuriosityEvent]:
        """Get events in a session."""
        from sqlalchemy import select
        from app.db.models_events import CuriosityEventDB

        async with self._session_factory() as session:
            result = await session.execute(
                select(CuriosityEventDB)
                .where(CuriosityEventDB.session_id == session_id)
                .order_by(CuriosityEventDB.timestamp)
            )
            return [self._db_to_event(e) for e in result.scalars()]

    async def get_events_between(
        self,
        child_id: str,
        start: datetime,
        end: datetime,
    ) -> List[CuriosityEvent]:
        """Get events in a time range."""
        from sqlalchemy import select, and_
        from app.db.models_events import CuriosityEventDB

        async with self._session_factory() as session:
            result = await session.execute(
                select(CuriosityEventDB)
                .where(and_(
                    CuriosityEventDB.child_id == child_id,
                    CuriosityEventDB.timestamp >= start,
                    CuriosityEventDB.timestamp <= end,
                ))
                .order_by(CuriosityEventDB.timestamp)
            )
            return [self._db_to_event(e) for e in result.scalars()]

    async def get_events_by_type(
        self,
        child_id: str,
        event_type: str,
        limit: Optional[int] = None,
    ) -> List[CuriosityEvent]:
        """Get events of a specific type."""
        from sqlalchemy import select, and_
        from app.db.models_events import CuriosityEventDB

        async with self._session_factory() as session:
            query = (
                select(CuriosityEventDB)
                .where(and_(
                    CuriosityEventDB.child_id == child_id,
                    CuriosityEventDB.event_type == event_type,
                ))
                .order_by(CuriosityEventDB.timestamp.desc())
            )
            if limit:
                query = query.limit(limit)

            result = await session.execute(query)
            return [self._db_to_event(e) for e in result.scalars()]

    async def get_cascade_chain(self, event_id: str) -> List[CuriosityEvent]:
        """Get cascade chain recursively."""
        from sqlalchemy import select
        from app.db.models_events import CuriosityEventDB

        result = []
        event = await self.get_event(event_id)
        if not event:
            return result

        result.append(event)

        # Find triggered events
        async with self._session_factory() as session:
            query_result = await session.execute(
                select(CuriosityEventDB)
                .where(CuriosityEventDB.triggered_by == event_id)
                .order_by(CuriosityEventDB.timestamp)
            )
            for db_event in query_result.scalars():
                result.extend(await self.get_cascade_chain(db_event.id))

        return result

    async def get_event_count(self, child_id: str) -> int:
        """Get event count for a child."""
        from sqlalchemy import select, func
        from app.db.models_events import CuriosityEventDB

        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count(CuriosityEventDB.id))
                .where(CuriosityEventDB.child_id == child_id)
            )
            return result.scalar() or 0
