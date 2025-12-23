"""
Supporting Models.

Additional models that support the core functionality:
- VideoScenario: Uploaded behavioral videos
- BaselineVideoRequest: Personalized video filming guidelines
- DevelopmentalMilestone: Tracking milestone achievements
- JournalEntry: Parent journal/diary entries
- Curiosity: Active curiosity threads (what Darshan wonders about)
- Investigation: Investigation context for curiosities
- InvestigationEvidence: Evidence collected during investigations
- DarshanJournal: Session-level journal entries
- DarshanCrystal: Developmental portrait data
- SessionHistory: Conversation history
- SharedSummary: Professional summaries
- SessionFlags: Session state flags
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    VideoStatus,
    CuriosityType,
)

if TYPE_CHECKING:
    from app.db.models_core import Child, Observation
    from app.db.models_auth import User


# =============================================================================
# Investigation Models (for Curiosity investigations)
# =============================================================================

class Investigation(Base, TimestampMixin):
    """
    Investigation - context for actively investigating a curiosity.

    Contains evidence collection and video workflow state.
    Linked to a Curiosity when actively investigating.
    """

    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    curiosity_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active/complete/stale
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)

    # Video workflow
    video_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    video_declined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    video_suggested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    guidelines_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # generating/ready/error

    # Relationships
    evidence: Mapped[List["InvestigationEvidence"]] = relationship(
        "InvestigationEvidence", back_populates="investigation", cascade="all, delete-orphan"
    )
    video_scenarios: Mapped[List["VideoScenario"]] = relationship(
        "VideoScenario", back_populates="investigation"
    )

    __table_args__ = (
        Index("ix_investigations_curiosity", "curiosity_id"),
    )

    def __repr__(self) -> str:
        return f"<Investigation {self.id} status={self.status}>"


class InvestigationEvidence(Base):
    """
    InvestigationEvidence - evidence collected during an investigation.

    Evidence can support, contradict, or transform the hypothesis.
    """

    __tablename__ = "investigation_evidence"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    effect: Mapped[str] = mapped_column(String(20), default="supports", nullable=False)  # supports/contradicts/transforms
    source: Mapped[str] = mapped_column(String(50), default="conversation", nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="evidence")

    __table_args__ = (
        Index("ix_evidence_investigation", "investigation_id"),
    )

    def __repr__(self) -> str:
        return f"<InvestigationEvidence {self.effect}: {self.content[:30]}...>"


# =============================================================================
# Darshan Persistence Models
# =============================================================================

class DarshanJournal(Base):
    """
    DarshanJournal - session-level journal entries.

    What Darshan learned during a session.
    """

    __tablename__ = "darshan_journal"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Content
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    significance: Mapped[str] = mapped_column(String(20), default="routine", nullable=False)  # routine | notable | breakthrough
    entry_type: Mapped[str] = mapped_column(String(30), default="observation", nullable=False)

    # Temporal
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)

    def __repr__(self) -> str:
        return f"<DarshanJournal {self.entry_type}: {self.summary[:30]}...>"


class DarshanCrystal(Base, TimestampMixin):
    """
    DarshanCrystal - developmental portrait for a child.

    The crystallized understanding of who this child is.
    """

    __tablename__ = "darshan_crystals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Portrait data (JSON)
    portrait_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<DarshanCrystal child={self.child_id}>"


class SessionHistoryEntry(Base):
    """
    SessionHistoryEntry - conversation history entry.

    Stores the conversation turns for a child.
    """

    __tablename__ = "session_history"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Message content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user/assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Temporal
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)

    __table_args__ = (
        Index("ix_session_history_child_turn", "child_id", "turn_number"),
    )

    def __repr__(self) -> str:
        return f"<SessionHistoryEntry {self.role} turn={self.turn_number}>"


class SharedSummary(Base):
    """
    SharedSummary - professional summaries shared externally.

    Stores professional and parent summaries.
    """

    __tablename__ = "shared_summaries"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Content
    summary_type: Mapped[str] = mapped_column(String(50), nullable=False)  # professional, parent, etc.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_metadata: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)  # JSON metadata

    # Temporal
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)

    def __repr__(self) -> str:
        return f"<SharedSummary {self.summary_type} child={self.child_id}>"


class SessionFlags(Base, TimestampMixin):
    """
    SessionFlags - session state flags.

    Stores flags like guided collection mode, baseline video requested, etc.
    """

    __tablename__ = "session_flags"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Flags
    guided_collection_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    baseline_video_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    flags_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON for additional flags

    def __repr__(self) -> str:
        return f"<SessionFlags child={self.child_id}>"


class VideoScenario(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    VideoScenario - an uploaded behavioral observation video.

    Videos are uploaded by parents based on personalized guidelines.
    They are analyzed to extract observations.
    """

    __tablename__ = "video_scenarios"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(50), default="video/mp4", nullable=False)

    # Scenario info (from baseline video request)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'play', 'mealtime', 'social', etc.
    scenario_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    baseline_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("baseline_video_requests.id", ondelete="SET NULL"), nullable=True
    )

    # Upload info
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # VideoStatus
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Analysis results
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # TEMPORAL AWARENESS
    video_recorded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When the video was actually recorded (from metadata or user input)"
    )
    child_age_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Investigation link (for curiosity-driven video requests)
    investigation_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="video_scenarios")
    uploader: Mapped[Optional["User"]] = relationship("User")
    baseline_request: Mapped[Optional["BaselineVideoRequest"]] = relationship(
        "BaselineVideoRequest", back_populates="videos"
    )
    observations: Mapped[List["Observation"]] = relationship(
        "Observation", back_populates="source_video"
    )
    investigation: Mapped[Optional["Investigation"]] = relationship(
        "Investigation", back_populates="video_scenarios"
    )

    __table_args__ = (
        Index("ix_video_child", "child_id"),
        Index("ix_video_status", "status"),
        Index("ix_video_scenario_type", "scenario_type"),
        Index("ix_video_scenarios_investigation", "investigation_id"),
    )

    def __repr__(self) -> str:
        return f"<VideoScenario {self.scenario_type} child={self.child_id}>"


class BaselineVideoRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    BaselineVideoRequest - personalized video filming guidelines.

    Generated for the child based on their profile and our curiosities.
    Tells parents what specific scenarios to film.
    """

    __tablename__ = "baseline_video_requests"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Scenario details
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_he: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Instructions
    description: Mapped[str] = mapped_column(Text, nullable=False)
    description_he: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    filming_tips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    filming_tips_he: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Why we want this
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_domains: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Comma-separated

    # Priority
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1=highest
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # State
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Generation metadata
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    based_on_curiosities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of curiosity IDs

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="baseline_video_requests")
    videos: Mapped[List["VideoScenario"]] = relationship(
        "VideoScenario", back_populates="baseline_request"
    )

    __table_args__ = (
        Index("ix_baseline_video_child", "child_id"),
        Index("ix_baseline_video_completed", "is_completed"),
        Index("ix_baseline_video_priority", "priority"),
    )

    def __repr__(self) -> str:
        return f"<BaselineVideoRequest {self.scenario_type}: {self.title}>"


class DevelopmentalMilestone(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    DevelopmentalMilestone - tracking milestone achievements.

    Records when developmental milestones were achieved (or not yet achieved).
    """

    __tablename__ = "developmental_milestones"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Milestone identity
    milestone_code: Mapped[str] = mapped_column(String(50), nullable=False)  # 'GROSS_MOTOR_WALK', etc.
    milestone_name: Mapped[str] = mapped_column(String(200), nullable=False)
    milestone_name_he: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    subdomain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Expected age range
    expected_age_months_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_age_months_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Achievement status
    status: Mapped[str] = mapped_column(String(20), default="not_assessed", nullable=False)
    # 'not_assessed', 'not_yet', 'emerging', 'achieved', 'exceeded'

    # TEMPORAL AWARENESS
    achieved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When milestone was achieved"
    )
    child_age_months_at_achievement: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reported_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When parent reported this"
    )

    # Source
    reported_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("observations.id", ondelete="SET NULL"), nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="milestones")
    reporter: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_milestone_child", "child_id"),
        Index("ix_milestone_child_domain", "child_id", "domain"),
        Index("ix_milestone_code", "milestone_code"),
        Index("ix_milestone_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<DevelopmentalMilestone {self.milestone_code} status={self.status}>"


class JournalEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    JournalEntry - parent diary entries.

    Free-form notes from parents about their child.
    Can trigger observation extraction.
    """

    __tablename__ = "journal_entries"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Categorization
    entry_type: Mapped[str] = mapped_column(String(30), default="note", nullable=False)
    # 'note', 'milestone', 'concern', 'celebration', 'question'
    mood: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'positive', 'neutral', 'concerned'
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Comma-separated

    # TEMPORAL AWARENESS
    occurred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When the event in the journal entry happened"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When the entry was written"
    )

    # Author
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Processing
    observations_extracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="journal_entries")
    author: Mapped[Optional["User"]] = relationship("User")
    observations: Mapped[List["Observation"]] = relationship(
        "Observation", back_populates="source_journal"
    )

    __table_args__ = (
        Index("ix_journal_child", "child_id"),
        Index("ix_journal_recorded", "recorded_at"),
        Index("ix_journal_type", "entry_type"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry {self.entry_type} child={self.child_id}>"


class Curiosity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Curiosity - active threads of wonder.

    What is Darshan curious about regarding this child?
    Curiosities guide conversation and video requests.

    Now unified with Investigation support for full hypothesis tracking.
    """

    __tablename__ = "curiosities"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    focus: Mapped[str] = mapped_column(Text, nullable=False)  # What we're curious about
    curiosity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # CuriosityType enum
    domain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Priority
    pull: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0.0 - 1.0
    certainty: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)  # For hypotheses

    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    satisfied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    satisfaction_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Temporal
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    times_explored: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # NEW: Status for lifecycle (added by migration d3a7b8f1e29c)
    status: Mapped[str] = mapped_column(String(20), default="wondering", nullable=False)  # wondering/investigating/understood/dormant

    # NEW: Hypothesis-specific fields
    theory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For hypothesis: the theory to test
    video_appropriate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Can video test this?
    video_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # calibration/chain/discovery/reframe/relational
    video_value_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Why video would help
    question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For question type: the specific question
    domains_involved: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array for pattern type

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="curiosities")

    __table_args__ = (
        Index("ix_curiosity_child_active", "child_id", "is_active"),
        Index("ix_curiosity_pull", "pull"),
        Index("ix_curiosity_type", "curiosity_type"),
        Index("ix_curiosities_child_status", "child_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Curiosity {self.curiosity_type}: {self.focus[:50]}...>"
