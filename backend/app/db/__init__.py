"""
Database Package - SQLAlchemy ORM Models and Repository Layer.

This package contains all database models for Chitta, organized into:
- base: Common configuration, mixins, enums
- models_auth: Users, OAuth, tokens
- models_access: Families, access control, sharing
- models_core: Children, sessions, messages, observations
- models_exploration: Explorations, evidence, stories
- models_synthesis: Crystals, patterns, portraits
- models_supporting: Videos, milestones, journal, curiosities
- repositories: Data access layer (Repository pattern)
- dependencies: FastAPI dependency injection
"""

# Base configuration
from app.db.base import (
    Base,
    engine,
    AsyncSessionLocal,
    get_db,
    get_database_url,
    create_engine_and_session,
    # Mixins
    TimestampMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    # Enums
    UserRole,
    ChildAccessRole,
    SessionType,
    ObservationSource,
    CuriosityType,
    ExplorationStatus,
    EvidenceRelation,
    StoryStatus,
    PatternStatus,
    CrystalStatus,
    ArtifactType,
    VideoStatus,
    InvitationStatus,
    AuditAction,
)

# Auth models
from app.db.models_auth import (
    User,
    OAuthAccount,
    RefreshToken,
    EmailVerificationToken,
    PasswordResetToken,
    AuditLog,
)

# Access models
from app.db.models_access import (
    Family,
    FamilyMember,
    ChildAccess,
    SharedArtifact,
    Invitation,
)

# Core models
from app.db.models_core import (
    Child,
    Session,
    Message,
    Observation,
)

# Exploration models
from app.db.models_exploration import (
    Exploration,
    ExplorationHistory,
    Evidence,
    Story,
    StoryDomain,
    StoryReveal,
)

# Synthesis models
from app.db.models_synthesis import (
    Pattern,
    PatternDomain,
    Crystal,
    CrystalPattern,
    PortraitSection,
    InterventionPathway,
)

# Supporting models
from app.db.models_supporting import (
    VideoScenario,
    BaselineVideoRequest,
    DevelopmentalMilestone,
    JournalEntry,
    Curiosity,
)

# Repository layer
from app.db.repositories import UnitOfWork

# FastAPI dependencies
from app.db.dependencies import (
    get_uow,
    get_uow_autocommit,
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
    get_current_admin_user,
    ChildAccessChecker,
    FamilyAccessChecker,
    require_child_chat,
    require_child_observations,
    require_child_clinical,
    require_child_manage,
    require_family_owner,
    require_family_parent,
)


# All models for Alembic
__all__ = [
    # Base
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    # Enums
    "UserRole",
    "ChildAccessRole",
    "SessionType",
    "ObservationSource",
    "CuriosityType",
    "ExplorationStatus",
    "EvidenceRelation",
    "StoryStatus",
    "PatternStatus",
    "CrystalStatus",
    "ArtifactType",
    "VideoStatus",
    "InvitationStatus",
    "AuditAction",
    # Auth
    "User",
    "OAuthAccount",
    "RefreshToken",
    "EmailVerificationToken",
    "PasswordResetToken",
    "AuditLog",
    # Access
    "Family",
    "FamilyMember",
    "ChildAccess",
    "SharedArtifact",
    "Invitation",
    # Core
    "Child",
    "Session",
    "Message",
    "Observation",
    # Exploration
    "Exploration",
    "ExplorationHistory",
    "Evidence",
    "Story",
    "StoryDomain",
    "StoryReveal",
    # Synthesis
    "Pattern",
    "PatternDomain",
    "Crystal",
    "CrystalPattern",
    "PortraitSection",
    "InterventionPathway",
    # Supporting
    "VideoScenario",
    "BaselineVideoRequest",
    "DevelopmentalMilestone",
    "JournalEntry",
    "Curiosity",
    # Repository
    "UnitOfWork",
    # Dependencies
    "get_uow",
    "get_uow_autocommit",
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_current_admin_user",
    "ChildAccessChecker",
    "FamilyAccessChecker",
    "require_child_chat",
    "require_child_observations",
    "require_child_clinical",
    "require_child_manage",
    "require_family_owner",
    "require_family_parent",
]
