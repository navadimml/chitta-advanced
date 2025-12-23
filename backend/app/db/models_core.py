"""
Core Domain Models.

The foundational models for Chitta:
- Child (the subject of observation)
- Session (conversation context)
- Message (chat history)
- Observation (what we notice about the child)
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Date, Text, ForeignKey, Index, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    SessionType,
    ObservationSource,
)

if TYPE_CHECKING:
    from app.db.models_access import Family, ChildAccess, SharedArtifact, Invitation
    from app.db.models_auth import User
    from app.db.models_synthesis import Crystal, Pattern, PortraitSection
    from app.db.models_supporting import (
        DevelopmentalMilestone, JournalEntry, VideoScenario,
        BaselineVideoRequest, Curiosity
    )


class Child(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Child - the subject of developmental observation.

    Contains profile information and temporal awareness markers.
    All observations, stories, patterns, and crystals link back to a child.
    """

    __tablename__ = "children"

    # Family relationship
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="CASCADE"), nullable=False
    )

    # Identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'male', 'female', 'other'

    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Medical/developmental context (optional, disclosed by parent)
    gestational_weeks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    birth_weight_grams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    known_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Free text from parent
    current_therapies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Free text

    # Workflow state
    intake_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    baseline_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Temporal awareness - when was understanding last updated
    last_observation_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_crystal_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_pattern_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    family: Mapped["Family"] = relationship("Family", back_populates="children")
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="child", cascade="all, delete-orphan"
    )
    observations: Mapped[List["Observation"]] = relationship(
        "Observation", back_populates="child", cascade="all, delete-orphan"
    )
    patterns: Mapped[List["Pattern"]] = relationship(
        "Pattern", back_populates="child", cascade="all, delete-orphan"
    )
    crystals: Mapped[List["Crystal"]] = relationship(
        "Crystal", back_populates="child", cascade="all, delete-orphan"
    )
    milestones: Mapped[List["DevelopmentalMilestone"]] = relationship(
        "DevelopmentalMilestone", back_populates="child", cascade="all, delete-orphan"
    )
    journal_entries: Mapped[List["JournalEntry"]] = relationship(
        "JournalEntry", back_populates="child", cascade="all, delete-orphan"
    )
    video_scenarios: Mapped[List["VideoScenario"]] = relationship(
        "VideoScenario", back_populates="child", cascade="all, delete-orphan"
    )
    baseline_video_requests: Mapped[List["BaselineVideoRequest"]] = relationship(
        "BaselineVideoRequest", back_populates="child", cascade="all, delete-orphan"
    )
    curiosities: Mapped[List["Curiosity"]] = relationship(
        "Curiosity", back_populates="child", cascade="all, delete-orphan"
    )
    portrait_sections: Mapped[List["PortraitSection"]] = relationship(
        "PortraitSection", back_populates="child", cascade="all, delete-orphan"
    )
    access_grants: Mapped[List["ChildAccess"]] = relationship(
        "ChildAccess", back_populates="child", cascade="all, delete-orphan"
    )
    shared_artifacts: Mapped[List["SharedArtifact"]] = relationship(
        "SharedArtifact", back_populates="child", cascade="all, delete-orphan"
    )
    invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation", back_populates="child", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_child_family", "family_id"),
        Index("ix_child_name", "name"),
    )

    @property
    def age_months(self) -> Optional[int]:
        """Calculate age in months if birth_date is set."""
        if not self.birth_date:
            return None
        today = date.today()
        months = (today.year - self.birth_date.year) * 12
        months += today.month - self.birth_date.month
        if today.day < self.birth_date.day:
            months -= 1
        return max(0, months)

    def __repr__(self) -> str:
        return f"<Child {self.name} id={self.id}>"


class Session(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Session - a conversation context.

    Sessions group messages and track conversation state.
    A child can have multiple sessions (with different users).
    Sessions auto-split after 4+ hour gaps.
    """

    __tablename__ = "sessions"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Session type (parent vs clinician vs intake)
    session_type: Mapped[str] = mapped_column(String(20), default="parent", nullable=False)

    # Conversation state
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Memory (session-level summary after distillation)
    memory_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    memory_distilled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Turn guidance state
    current_focus: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    exploration_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="sessions")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="sessions")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_session_child", "child_id"),
        Index("ix_session_user", "user_id"),
        Index("ix_session_last_activity", "last_activity_at"),
    )

    @property
    def is_active(self) -> bool:
        """Session is active if no explicit end and recent activity."""
        if self.ended_at:
            return False
        from datetime import timezone
        now = datetime.now(timezone.utc)
        hours_since_activity = (now - self.last_activity_at).total_seconds() / 3600
        return hours_since_activity < 4  # 4 hour threshold

    def __repr__(self) -> str:
        return f"<Session child={self.child_id} type={self.session_type}>"


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Message - a single chat message.

    Stores both user messages and assistant responses.
    Links to observations extracted from this message.
    """

    __tablename__ = "messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Message content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Ordering
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Metadata
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # LLM metadata (for assistant messages)
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    observations: Mapped[List["Observation"]] = relationship(
        "Observation", back_populates="source_message"
    )

    __table_args__ = (
        Index("ix_message_session_seq", "session_id", "sequence_number"),
    )

    def __repr__(self) -> str:
        return f"<Message {self.role} session={self.session_id} seq={self.sequence_number}>"


class Observation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Observation - what we notice about the child.

    Observations are facts extracted from conversations, videos, or journal entries.
    They are domain-tagged and temporally aware.

    Key temporal fields:
    - t_valid: When this was TRUE in the real world
    - t_created: When we recorded this observation
    """

    __tablename__ = "observations"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)  # 'motor', 'language', 'social', etc.
    subdomain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'gross_motor', 'fine_motor'

    # Source tracking
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)  # ObservationSource enum
    source_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    source_video_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("video_scenarios.id", ondelete="SET NULL"), nullable=True
    )
    source_journal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True
    )

    # Who recorded it
    recorded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # TEMPORAL AWARENESS - Critical fields from the graph model
    t_valid: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When this was TRUE in the real world"
    )
    t_valid_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When this stopped being true (if known)"
    )
    t_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When we recorded this observation"
    )

    # Age context (child's age when this was observed)
    child_age_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Confidence/quality
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    is_clinical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="observations")
    source_message: Mapped[Optional["Message"]] = relationship("Message", back_populates="observations")
    source_video: Mapped[Optional["VideoScenario"]] = relationship("VideoScenario", back_populates="observations")
    source_journal: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry", back_populates="observations")
    recorder: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_observation_child_domain", "child_id", "domain"),
        Index("ix_observation_child_created", "child_id", "t_created"),
        Index("ix_observation_t_valid", "t_valid"),
        Index("ix_observation_source_type", "source_type"),
    )

    def __repr__(self) -> str:
        return f"<Observation {self.domain}: {self.content[:50]}...>"
