"""
SQLAlchemy Base Configuration and Common Mixins.

Provides the foundation for all database models including:
- Async engine configuration
- Base model class with common fields
- Reusable mixins for timestamps, soft delete, etc.
- Common enums used across models
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Boolean, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# =============================================================================
# ENUMS
# =============================================================================

class UserRole(str, enum.Enum):
    """User roles within a family."""
    OWNER = "owner"          # Full control, can delete family
    PARENT = "parent"        # Full access to all children
    CAREGIVER = "caregiver"  # Can add observations, limited settings


class ChildAccessRole(str, enum.Enum):
    """Roles for child-specific access (non-family members)."""
    CLINICIAN = "clinician"
    THERAPIST = "therapist"
    SPECIALIST = "specialist"
    TEACHER = "teacher"
    VIEWER = "viewer"


class SessionType(str, enum.Enum):
    """Type of conversation session."""
    PARENT = "parent"
    CLINICIAN = "clinician"
    INTAKE = "intake"


class ObservationSource(str, enum.Enum):
    """Source of an observation."""
    PARENT_REPORT = "parent_report"
    CLINICAL_OBSERVATION = "clinical_observation"
    VIDEO_ANALYSIS = "video_analysis"
    JOURNAL = "journal"


class CuriosityType(str, enum.Enum):
    """Four types of curiosity exploration."""
    DISCOVERY = "discovery"    # Open receiving
    QUESTION = "question"      # Following a thread
    HYPOTHESIS = "hypothesis"  # Testing a theory
    PATTERN = "pattern"        # Connecting dots


class ExplorationStatus(str, enum.Enum):
    """Status of an exploration."""
    ACTIVE = "active"
    SATISFIED = "satisfied"
    SUPERSEDED = "superseded"
    DORMANT = "dormant"


class EvidenceRelation(str, enum.Enum):
    """How evidence relates to an exploration."""
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    COMPLICATES = "complicates"
    SUPERSEDES = "supersedes"


class StoryStatus(str, enum.Enum):
    """Status of a captured story."""
    CAPTURED = "captured"
    INTEGRATED = "integrated"
    ARCHIVED = "archived"


class PatternStatus(str, enum.Enum):
    """Status of a detected pattern."""
    EMERGING = "emerging"
    ESTABLISHED = "established"
    EVOLVING = "evolving"
    RESOLVED = "resolved"


class CrystalStatus(str, enum.Enum):
    """Status of a crystal (synthesized understanding)."""
    FORMING = "forming"
    STABLE = "stable"
    EVOLVING = "evolving"
    STALE = "stale"


class ArtifactType(str, enum.Enum):
    """Types of artifacts that can be shared."""
    CRYSTAL = "crystal"
    REPORT = "report"
    PORTRAIT = "portrait"
    VIDEO_ANALYSIS = "video_analysis"


class VideoStatus(str, enum.Enum):
    """Status of an uploaded video."""
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class InvitationStatus(str, enum.Enum):
    """Status of an invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    LOGIN = "login"
    LOGOUT = "logout"
    CHILD_CREATE = "child_create"
    CHILD_UPDATE = "child_update"
    OBSERVATION_ADD = "observation_add"
    ACCESS_GRANT = "access_grant"
    ACCESS_REVOKE = "access_revoke"
    ARTIFACT_SHARE = "artifact_share"
    REPORT_GENERATE = "report_generate"
    REPORT_DOWNLOAD = "report_download"


# =============================================================================
# BASE CLASS
# =============================================================================

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# =============================================================================
# MIXINS
# =============================================================================

class TimestampMixin:
    """Adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )


class SoftDeleteMixin:
    """Adds soft delete capability."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class UUIDPrimaryKeyMixin:
    """Adds UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_database_url(async_mode: bool = True) -> str:
    """
    Get database URL from environment.

    Supports:
    - PostgreSQL (production): postgresql+asyncpg://...
    - SQLite (development): sqlite+aiosqlite:///...
    """
    import os

    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chitta.db")

    # Handle Render's postgres:// vs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and async_mode:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return database_url


def create_engine_and_session():
    """Create async engine and session factory."""

    database_url = get_database_url()

    # SQLite needs special handling
    connect_args = {}
    if "sqlite" in database_url:
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        connect_args=connect_args if connect_args else {}
    )

    async_session = async_sessionmaker(
        engine,
        expire_on_commit=False
    )

    return engine, async_session


# Global instances (initialized on first import)
engine, AsyncSessionLocal = create_engine_and_session()


async def get_db():
    """Dependency for FastAPI to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
