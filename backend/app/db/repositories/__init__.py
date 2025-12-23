"""
Repository Layer - Data Access Abstraction.

Provides a clean interface for data access operations,
abstracting away SQLAlchemy details from application code.

Main entry point is the UnitOfWork class:

    async with UnitOfWork() as uow:
        user = await uow.users.create_user(...)
        child = await uow.children.create_child(...)
        await uow.commit()
"""

# Unit of Work (main entry point)
from app.db.repositories.unit_of_work import UnitOfWork

# Base repository
from app.db.repositories.base import BaseRepository

# Auth repositories
from app.db.repositories.users import (
    UserRepository,
    OAuthAccountRepository,
    RefreshTokenRepository,
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    AuditLogRepository,
)

# Access repositories
from app.db.repositories.families import (
    FamilyRepository,
    FamilyMemberRepository,
    ChildAccessRepository,
    SharedArtifactRepository,
    InvitationRepository,
)

# Core repositories
from app.db.repositories.children import ChildRepository
from app.db.repositories.sessions import SessionRepository, MessageRepository
from app.db.repositories.observations import ObservationRepository


# Synthesis repositories
from app.db.repositories.synthesis import (
    PatternRepository,
    CrystalRepository,
    PortraitSectionRepository,
    InterventionPathwayRepository,
)


__all__ = [
    # Unit of Work
    "UnitOfWork",
    # Base
    "BaseRepository",
    # Auth
    "UserRepository",
    "OAuthAccountRepository",
    "RefreshTokenRepository",
    "EmailVerificationTokenRepository",
    "PasswordResetTokenRepository",
    "AuditLogRepository",
    # Access
    "FamilyRepository",
    "FamilyMemberRepository",
    "ChildAccessRepository",
    "SharedArtifactRepository",
    "InvitationRepository",
    # Core
    "ChildRepository",
    "SessionRepository",
    "MessageRepository",
    "ObservationRepository",
    # Synthesis
    "PatternRepository",
    "CrystalRepository",
    "PortraitSectionRepository",
    "InterventionPathwayRepository",
]
