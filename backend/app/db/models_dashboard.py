"""
Dashboard Models for Expert Review and Feedback.

Provides models for:
- CognitiveTurn: Complete cognitive trace for a conversation turn
- ClinicalNote: Team-visible annotations on any element
- InferenceFlag: Flag incorrect AI inferences with resolution workflow
- CertaintyAdjustment: Audit trail for expert certainty adjustments
- ExpertEvidence: Evidence added by clinical experts (not from conversation)
- ExpertCorrection: Structured corrections to AI decisions
- MissedSignal: Signals that expert says should have been caught
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Index, Float, Integer, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# =============================================================================
# ENUMS
# =============================================================================

class NoteType(str, enum.Enum):
    """Types of clinical notes."""
    ANNOTATION = "annotation"    # General observation
    CORRECTION = "correction"    # Suggested fix
    GUIDANCE = "guidance"        # Clinical guidance for system improvement


class FlagType(str, enum.Enum):
    """Types of inference flags."""
    INCORRECT = "incorrect"      # Clearly wrong inference
    UNCERTAIN = "uncertain"      # Needs verification
    NEEDS_REVIEW = "needs_review"  # Should be reviewed by another expert


class TargetType(str, enum.Enum):
    """Types of elements that can be annotated or flagged."""
    CURIOSITY = "curiosity"
    OBSERVATION = "observation"
    PATTERN = "pattern"
    CRYSTAL = "crystal"
    EVIDENCE = "evidence"
    CONVERSATION_TURN = "conversation_turn"
    MILESTONE = "milestone"


class EvidenceEffect(str, enum.Enum):
    """Effect of evidence on curiosity certainty."""
    SUPPORTS = "supports"        # +0.1 to certainty
    CONTRADICTS = "contradicts"  # -0.15 to certainty
    TRANSFORMS = "transforms"    # Reset to 0.4


class CorrectionType(str, enum.Enum):
    """Types of expert corrections."""
    DOMAIN_CHANGE = "domain_change"          # Wrong developmental domain
    EXTRACTION_ERROR = "extraction_error"    # Observation text is wrong
    MISSED_SIGNAL = "missed_signal"          # Should have noticed something
    HALLUCINATION = "hallucination"          # AI invented something
    EVIDENCE_RECLASSIFY = "evidence_reclassify"  # Wrong supports/contradicts
    TIMING_ISSUE = "timing_issue"            # Video suggested too early/late
    CERTAINTY_ADJUSTMENT = "certainty_adjustment"  # Delta too high/low
    RESPONSE_ISSUE = "response_issue"        # Problem with AI response


class CorrectionSeverity(str, enum.Enum):
    """Severity of corrections for training prioritization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# MODELS
# =============================================================================


class CognitiveTurn(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Complete cognitive trace for one conversation turn.

    This is the core data structure for the Cognitive Dashboard.
    Captures the AI's full "thinking" for a single turn.
    """

    __tablename__ = "cognitive_turns"

    # Identity
    turn_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Input
    parent_message: Mapped[str] = mapped_column(Text, nullable=False)
    parent_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Phase 1: Perception (stored as JSON)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    perceived_intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # State changes (stored as JSON)
    state_delta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Phase 2: Response
    turn_guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active_curiosities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of focus strings
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_cognitive_turns_child", "child_id"),
        Index("ix_cognitive_turns_child_number", "child_id", "turn_number"),
        Index("ix_cognitive_turns_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<CognitiveTurn {self.turn_id} (#{self.turn_number}) for child {self.child_id}>"


class ExpertCorrection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Structured correction to an AI decision.

    Expert provides:
    - What was wrong (correction_type)
    - Original vs corrected value
    - Clinical reasoning (GOLD for training)

    These corrections become training data for improving the AI.
    """

    __tablename__ = "expert_corrections"

    # Link to turn
    turn_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Target element within the turn
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # observation, curiosity, hypothesis, evidence, video
    target_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Optional specific element ID

    # Correction details
    correction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    corrected_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Expert reasoning - THIS IS GOLD for training
    expert_reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    # Author
    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    expert_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Training pipeline
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    used_in_training: Mapped[bool] = mapped_column(default=False, nullable=False)
    training_batch_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_expert_corrections_turn", "turn_id"),
        Index("ix_expert_corrections_child", "child_id"),
        Index("ix_expert_corrections_type", "correction_type"),
        Index("ix_expert_corrections_unused", "used_in_training"),
    )

    def __repr__(self) -> str:
        return f"<ExpertCorrection {self.id} ({self.correction_type}) on turn {self.turn_id}>"


class MissedSignal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Signal that expert says should have been caught.

    When AI misses something important in the parent's message,
    experts can document what should have been noticed.
    """

    __tablename__ = "missed_signals"

    # Link to turn
    turn_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # What was missed
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)  # observation, curiosity, hypothesis
    content: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Expert explanation
    why_important: Mapped[str] = mapped_column(Text, nullable=False)

    # Author
    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    expert_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_missed_signals_turn", "turn_id"),
        Index("ix_missed_signals_child", "child_id"),
        Index("ix_missed_signals_type", "signal_type"),
    )

    def __repr__(self) -> str:
        return f"<MissedSignal {self.id} ({self.signal_type}) on turn {self.turn_id}>"

class ClinicalNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Team-visible annotation on any Darshan element.

    Notes are visible only to team members (admins) and do not
    directly affect the AI's understanding.
    """

    __tablename__ = "clinical_notes"

    # Target reference
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(200), nullable=False)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(20), default="annotation", nullable=False)

    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Indexes
    __table_args__ = (
        Index("ix_clinical_notes_child", "child_id"),
        Index("ix_clinical_notes_target", "target_type", "target_id"),
        Index("ix_clinical_notes_author", "author_id"),
    )

    def __repr__(self) -> str:
        return f"<ClinicalNote {self.id} on {self.target_type}:{self.target_id}>"


class InferenceFlag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Flag indicating an incorrect or uncertain AI inference.

    Supports a resolution workflow where flags can be reviewed
    and resolved by team members.
    """

    __tablename__ = "inference_flags"

    # Target reference
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(200), nullable=False)
    target_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Human-readable content

    # Flag details
    flag_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    resolved_by_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_inference_flags_child", "child_id"),
        Index("ix_inference_flags_target", "target_type", "target_id"),
        Index("ix_inference_flags_unresolved", "child_id", "resolved_at"),
        Index("ix_inference_flags_author", "author_id"),
    )

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def __repr__(self) -> str:
        status = "resolved" if self.is_resolved else "open"
        return f"<InferenceFlag {self.id} [{status}] on {self.target_type}:{self.target_id}>"


class CertaintyAdjustment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Audit trail for expert certainty adjustments.

    Records every time an expert manually adjusts the certainty
    of a curiosity or pattern.
    """

    __tablename__ = "certainty_adjustments"

    # Target reference
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    curiosity_focus: Mapped[str] = mapped_column(String(500), nullable=False)

    # Values
    original_certainty: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_certainty: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_certainty_adjustments_child", "child_id"),
        Index("ix_certainty_adjustments_author", "author_id"),
    )

    @property
    def delta(self) -> float:
        """The change in certainty."""
        return self.adjusted_certainty - self.original_certainty

    def __repr__(self) -> str:
        return f"<CertaintyAdjustment {self.original_certainty:.2f} -> {self.adjusted_certainty:.2f}>"


class ExpertEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Evidence added by clinical expert (not from conversation).

    This evidence is added to curiosity investigations and affects
    certainty calculations.
    """

    __tablename__ = "expert_evidence"

    # Target reference
    child_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    curiosity_focus: Mapped[str] = mapped_column(String(500), nullable=False)

    # Evidence details
    content: Mapped[str] = mapped_column(Text, nullable=False)
    effect: Mapped[str] = mapped_column(String(20), nullable=False)  # supports, contradicts, transforms

    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Track if applied to Darshan
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Indexes
    __table_args__ = (
        Index("ix_expert_evidence_child", "child_id"),
        Index("ix_expert_evidence_curiosity", "child_id", "curiosity_focus"),
        Index("ix_expert_evidence_author", "author_id"),
    )

    @property
    def is_applied(self) -> bool:
        return self.applied_at is not None

    def __repr__(self) -> str:
        return f"<ExpertEvidence {self.effect} for '{self.curiosity_focus[:30]}...'>"
