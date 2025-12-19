"""
Synthesis Models - Crystallized Understanding.

When understanding matures, it crystallizes into:
- Pattern: Cross-domain connections observed over time
- Crystal: Synthesized understanding of who the child IS
- PortraitSection: Structured sections for professional summaries
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
    UUIDPrimaryKeyMixin,
    PatternStatus,
    CrystalStatus,
)

if TYPE_CHECKING:
    from app.db.models_core import Child


class Pattern(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Pattern - cross-domain connections.

    Patterns emerge from synthesis - connecting dots across domains.
    Example: "Sensory seeking behaviors appear across motor, social, and regulation"

    Key temporal fields:
    - detected_at: When pattern was first noticed
    - last_confirmed_at: Last time evidence supported this pattern
    - based_on_observations_through: Staleness marker
    """

    __tablename__ = "patterns"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    description: Mapped[str] = mapped_column(Text, nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'sensory_seeking', 'regulation', etc.
    significance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # State
    status: Mapped[str] = mapped_column(String(20), default="emerging", nullable=False)  # PatternStatus
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # TEMPORAL AWARENESS
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When this pattern was first detected"
    )
    last_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When evidence last supported this pattern"
    )
    based_on_observations_through: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Timestamp of most recent observation considered"
    )

    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="patterns")
    domains: Mapped[List["PatternDomain"]] = relationship(
        "PatternDomain", back_populates="pattern", cascade="all, delete-orphan"
    )
    crystal_links: Mapped[List["CrystalPattern"]] = relationship(
        "CrystalPattern", back_populates="pattern", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_pattern_child_status", "child_id", "status"),
        Index("ix_pattern_type", "pattern_type"),
        Index("ix_pattern_detected", "detected_at"),
    )

    def __repr__(self) -> str:
        return f"<Pattern {self.pattern_type}: {self.description[:50]}...>"


class PatternDomain(Base, UUIDPrimaryKeyMixin):
    """
    PatternDomain - domains involved in a pattern.

    Patterns span multiple domains. This tracks which ones.
    """

    __tablename__ = "pattern_domains"

    pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patterns.id", ondelete="CASCADE"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    manifestation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # How it shows in this domain

    # Relationships
    pattern: Mapped["Pattern"] = relationship("Pattern", back_populates="domains")

    __table_args__ = (
        Index("ix_pattern_domain_pattern", "pattern_id"),
        Index("ix_pattern_domain_unique", "pattern_id", "domain", unique=True),
    )


class Crystal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Crystal - synthesized understanding of the child.

    The crystal is a holistic view that emerges from synthesis.
    It represents "who this child IS" at a point in time.

    Key temporal fields:
    - synthesized_at: When this crystal was formed
    - based_on_observations_through: Staleness detection
    - valid_from/valid_until: Time range this crystal represents
    """

    __tablename__ = "crystals"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    previous_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crystals.id", ondelete="SET NULL"), nullable=True
    )

    # Content
    essence: Mapped[str] = mapped_column(Text, nullable=False)  # Core narrative: "Who is this child?"
    strengths_narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    growth_areas_narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    wonder_narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Open questions

    # State
    status: Mapped[str] = mapped_column(String(20), default="forming", nullable=False)  # CrystalStatus
    richness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # How complete

    # TEMPORAL AWARENESS
    synthesized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When this crystal was formed"
    )
    based_on_observations_through: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Timestamp of most recent observation included"
    )

    # What age/time this crystal represents
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Start of period this crystal represents"
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="End of period this crystal represents"
    )
    child_age_months_at_synthesis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Synthesis metadata
    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    story_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pattern_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="crystals")
    previous_version: Mapped[Optional["Crystal"]] = relationship(
        "Crystal", remote_side="Crystal.id"
    )
    patterns: Mapped[List["CrystalPattern"]] = relationship(
        "CrystalPattern", back_populates="crystal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_crystal_child", "child_id"),
        Index("ix_crystal_child_version", "child_id", "version"),
        Index("ix_crystal_synthesized", "synthesized_at"),
        Index("ix_crystal_status", "status"),
    )

    @property
    def is_stale(self) -> bool:
        """Crystal is stale if newer observations exist."""
        # Would be checked against child.last_observation_at
        return False

    def __repr__(self) -> str:
        return f"<Crystal child={self.child_id} v{self.version}>"


class CrystalPattern(Base, UUIDPrimaryKeyMixin):
    """
    CrystalPattern - links crystals to their component patterns.

    Tracks which patterns contributed to a crystal's synthesis.
    """

    __tablename__ = "crystal_patterns"

    crystal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crystals.id", ondelete="CASCADE"), nullable=False
    )
    pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patterns.id", ondelete="CASCADE"), nullable=False
    )

    # How pattern influenced crystal
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    crystal: Mapped["Crystal"] = relationship("Crystal", back_populates="patterns")
    pattern: Mapped["Pattern"] = relationship("Pattern", back_populates="crystal_links")

    __table_args__ = (
        Index("ix_crystal_pattern_crystal", "crystal_id"),
        Index("ix_crystal_pattern_unique", "crystal_id", "pattern_id", unique=True),
    )


class PortraitSection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    PortraitSection - structured output for professional summaries.

    Portraits are parent-facing or clinician-facing summaries
    generated from crystals and observations.
    """

    __tablename__ = "portrait_sections"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )
    crystal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crystals.id", ondelete="SET NULL"), nullable=True
    )

    # Section identity
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'overview', 'domain_summary', 'recommendations'
    section_key: Mapped[str] = mapped_column(String(50), nullable=False)  # 'motor', 'language', 'social', etc.
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_he: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Hebrew title
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_he: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Hebrew content

    # For clinical sections
    clinical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icd_codes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Comma-separated

    # Audience
    audience: Mapped[str] = mapped_column(String(20), default="parent", nullable=False)  # 'parent', 'clinician'

    # TEMPORAL AWARENESS
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    based_on_observations_through: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="portrait_sections")
    crystal: Mapped[Optional["Crystal"]] = relationship("Crystal")

    __table_args__ = (
        Index("ix_portrait_child_type", "child_id", "section_type"),
        Index("ix_portrait_child_audience", "child_id", "audience"),
        Index("ix_portrait_section_key", "section_key"),
    )

    def __repr__(self) -> str:
        return f"<PortraitSection {self.section_type}:{self.section_key}>"


class InterventionPathway(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    InterventionPathway - recommended next steps.

    Based on patterns and crystals, what interventions might help?
    """

    __tablename__ = "intervention_pathways"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )
    crystal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crystals.id", ondelete="SET NULL"), nullable=True
    )

    # Content
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # 'high', 'medium', 'low'

    # Provider type
    specialist_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'OT', 'SLP', 'psychologist'

    # State
    status: Mapped[str] = mapped_column(String(20), default="suggested", nullable=False)  # 'suggested', 'accepted', 'in_progress', 'completed'
    parent_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # TEMPORAL
    suggested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    child: Mapped["Child"] = relationship("Child")
    crystal: Mapped[Optional["Crystal"]] = relationship("Crystal")

    __table_args__ = (
        Index("ix_intervention_child", "child_id"),
        Index("ix_intervention_domain", "domain"),
        Index("ix_intervention_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<InterventionPathway {self.domain}: {self.recommendation[:50]}...>"
