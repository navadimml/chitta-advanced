"""
Event Store Database Models.

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module provides the SQLAlchemy model for persisting curiosity events.
Events are immutable once written - this is append-only storage.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CuriosityEventDB(Base):
    """
    Database model for curiosity events.

    Events are immutable and append-only. They record every change
    to the curiosity system with full provenance tracking.

    Key fields:
    - entity_type/entity_id: What entity this event affects
    - event_type: What kind of change occurred
    - changes_json: The actual state changes (old → new)
    - reasoning: WHY this change was made (required for explainability)
    - evidence_refs: What observations led to this decision
    - triggered_by: Parent event in cascade chain (if any)
    """

    __tablename__ = "curiosity_events"

    # Primary key (UUID stored as string for SQLite compatibility)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Temporal
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When this event occurred"
    )

    # Context
    session_id: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Session in which this event occurred"
    )
    child_id: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Child this event belongs to"
    )

    # Event classification
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Type of event (observation_added, curiosity_created, etc.)"
    )
    entity_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="Type of entity affected (observation, curiosity, pattern, etc.)"
    )
    entity_id: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="ID of the entity affected by this event"
    )

    # State changes (stored as JSON)
    changes_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON object mapping field names to {from, to} changes"
    )

    # Provenance (REQUIRED for explainability)
    reasoning: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="WHY this change was made - natural language explanation"
    )
    evidence_refs_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON array of observation/evidence IDs that led to this decision"
    )

    # Cascade tracking
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True,
        comment="Parent event ID if this was triggered as part of a cascade"
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
        comment="When this record was created in the database"
    )

    __table_args__ = (
        # Primary queries
        Index("ix_curiosity_events_child", "child_id"),
        Index("ix_curiosity_events_session", "session_id"),
        Index("ix_curiosity_events_entity", "entity_id"),

        # Time-based queries
        Index("ix_curiosity_events_timestamp", "timestamp"),
        Index("ix_curiosity_events_child_time", "child_id", "timestamp"),

        # Type-based queries
        Index("ix_curiosity_events_type", "event_type"),
        Index("ix_curiosity_events_child_type", "child_id", "event_type"),

        # Cascade tracking
        Index("ix_curiosity_events_triggered_by", "triggered_by"),
    )

    def __repr__(self) -> str:
        return f"<CuriosityEvent {self.event_type} entity={self.entity_id}>"
