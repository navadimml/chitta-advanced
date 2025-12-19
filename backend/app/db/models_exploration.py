"""
Exploration and Story Models.

Captures how Darshan (the observing intelligence) explores and understands:
- Exploration: Active lines of inquiry (questions, hypotheses, patterns)
- ExplorationHistory: Temporal tracking of exploration changes
- Evidence: Links observations to explorations
- Story: Rich narratives captured from parent conversations
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    CuriosityType,
    ExplorationStatus,
    EvidenceRelation,
    StoryStatus,
)

if TYPE_CHECKING:
    from app.db.models_core import Child, Observation


class Exploration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Exploration - an active line of inquiry.

    Explorations represent what Darshan is curious about and exploring.
    They can be questions, hypotheses, discoveries, or patterns.

    Key temporal fields:
    - t_opened: When this exploration began
    - last_activated: When we last explored this
    - based_on_observations_through: Staleness detection marker
    """

    __tablename__ = "explorations"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # What we're exploring
    focus: Mapped[str] = mapped_column(Text, nullable=False)  # The question or hypothesis
    exploration_type: Mapped[str] = mapped_column(String(20), nullable=False)  # CuriosityType enum
    domain: Mapped[str] = mapped_column(String(50), nullable=False)  # 'motor', 'language', 'social', etc.
    subdomain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # State
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # ExplorationStatus
    certainty: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)  # 0.0 - 1.0
    pull: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # Priority/urgency

    # Context
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_exploration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("explorations.id", ondelete="SET NULL"), nullable=True
    )

    # TEMPORAL AWARENESS
    t_opened: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When this exploration was opened"
    )
    last_activated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When we last explored this"
    )
    times_explored: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Staleness detection - observations seen when last updated
    based_on_observations_through: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Timestamp of most recent observation when certainty was last updated"
    )

    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    superseded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("explorations.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="explorations")
    parent_exploration: Mapped[Optional["Exploration"]] = relationship(
        "Exploration", remote_side="Exploration.id", foreign_keys=[parent_exploration_id]
    )
    superseded_by: Mapped[Optional["Exploration"]] = relationship(
        "Exploration", remote_side="Exploration.id", foreign_keys=[superseded_by_id]
    )
    evidence_links: Mapped[List["Evidence"]] = relationship(
        "Evidence", back_populates="exploration", cascade="all, delete-orphan"
    )
    history: Mapped[List["ExplorationHistory"]] = relationship(
        "ExplorationHistory", back_populates="exploration", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_exploration_child_status", "child_id", "status"),
        Index("ix_exploration_child_domain", "child_id", "domain"),
        Index("ix_exploration_type", "exploration_type"),
        Index("ix_exploration_pull", "pull"),
    )

    @property
    def is_stale(self) -> bool:
        """Check if exploration might be outdated based on new observations."""
        if not self.based_on_observations_through:
            return True
        # Stale if there are newer observations (checked externally)
        return False

    def __repr__(self) -> str:
        return f"<Exploration {self.exploration_type}: {self.focus[:50]}...>"


class ExplorationHistory(Base, UUIDPrimaryKeyMixin):
    """
    ExplorationHistory - temporal tracking of exploration changes.

    Tracks how certainty and status evolve over time.
    Enables queries like "What did we believe in March?"
    """

    __tablename__ = "exploration_history"

    exploration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("explorations.id", ondelete="CASCADE"), nullable=False
    )

    # Snapshot of state at this point in time
    certainty: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    pull: Mapped[float] = mapped_column(Float, nullable=False)

    # When this state was recorded
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # What triggered this change
    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'evidence', 'manual', 'decay', 'synthesis'
    trigger_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("observations.id", ondelete="SET NULL"), nullable=True
    )
    trigger_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Change delta
    certainty_delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    exploration: Mapped["Exploration"] = relationship("Exploration", back_populates="history")
    trigger_observation: Mapped[Optional["Observation"]] = relationship("Observation")

    __table_args__ = (
        Index("ix_exploration_history_exploration", "exploration_id"),
        Index("ix_exploration_history_time", "recorded_at"),
    )

    def __repr__(self) -> str:
        return f"<ExplorationHistory exploration={self.exploration_id} certainty={self.certainty}>"


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Evidence - links observations to explorations.

    Represents how an observation affects an exploration's certainty.
    """

    __tablename__ = "evidence"

    exploration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("explorations.id", ondelete="CASCADE"), nullable=False
    )
    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("observations.id", ondelete="CASCADE"), nullable=False
    )

    # How this observation relates to the exploration
    relation: Mapped[str] = mapped_column(String(20), nullable=False)  # EvidenceRelation enum
    strength: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0.0 - 1.0
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # When evidence was linked
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    exploration: Mapped["Exploration"] = relationship("Exploration", back_populates="evidence_links")
    observation: Mapped["Observation"] = relationship("Observation", back_populates="evidence_links")

    __table_args__ = (
        Index("ix_evidence_exploration", "exploration_id"),
        Index("ix_evidence_observation", "observation_id"),
        Index("ix_evidence_unique", "exploration_id", "observation_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Evidence {self.relation} exploration={self.exploration_id}>"


class Story(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Story - rich narratives captured from conversations.

    Stories are parent-told narratives that reveal developmental context.
    They're richer than individual observations and may span multiple domains.

    Key temporal fields:
    - occurred_at: When the story happened in real life
    - recorded_at: When we captured it
    """

    __tablename__ = "stories"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # State
    status: Mapped[str] = mapped_column(String(20), default="captured", nullable=False)  # StoryStatus

    # TEMPORAL AWARENESS
    occurred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When this story happened in real life"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When we captured this story"
    )
    child_age_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Source
    source_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True
    )

    # Emotional tone
    emotional_tone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'concern', 'pride', 'wonder'
    parent_interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="stories")
    domains: Mapped[List["StoryDomain"]] = relationship(
        "StoryDomain", back_populates="story", cascade="all, delete-orphan"
    )
    reveals: Mapped[List["StoryReveal"]] = relationship(
        "StoryReveal", back_populates="story", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_story_child", "child_id"),
        Index("ix_story_occurred", "occurred_at"),
        Index("ix_story_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Story {self.title}>"


class StoryDomain(Base, UUIDPrimaryKeyMixin):
    """
    StoryDomain - links stories to developmental domains.

    A story can span multiple domains (e.g., a playground story
    might reveal both motor and social aspects).
    """

    __tablename__ = "story_domains"

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    relevance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="domains")

    __table_args__ = (
        Index("ix_story_domain_story", "story_id"),
        Index("ix_story_domain_unique", "story_id", "domain", unique=True),
    )


class StoryReveal(Base, UUIDPrimaryKeyMixin):
    """
    StoryReveal - specific insights extracted from a story.

    What does this story reveal about the child?
    """

    __tablename__ = "story_reveals"

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )

    # What was revealed
    insight: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="reveals")

    __table_args__ = (
        Index("ix_story_reveal_story", "story_id"),
    )
