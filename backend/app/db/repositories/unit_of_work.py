"""
Unit of Work - Transaction Management.

Provides a single entry point for all repository operations
with transaction management (commit/rollback).

Usage:
    async with UnitOfWork() as uow:
        user = await uow.users.create_user(...)
        family = await uow.families.create_family(...)
        await uow.commit()

If an exception occurs, changes are automatically rolled back.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal

# Import all repositories
from app.db.repositories.users import (
    UserRepository,
    OAuthAccountRepository,
    RefreshTokenRepository,
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    AuditLogRepository,
)
from app.db.repositories.families import (
    FamilyRepository,
    FamilyMemberRepository,
    ChildAccessRepository,
    SharedArtifactRepository,
    InvitationRepository,
)
from app.db.repositories.children import ChildRepository
from app.db.repositories.sessions import SessionRepository, MessageRepository
from app.db.repositories.observations import ObservationRepository
from app.db.repositories.synthesis import (
    PatternRepository,
    CrystalRepository,
    PortraitSectionRepository,
    InterventionPathwayRepository,
)
from app.db.repositories.darshan import DarshanRepository


class UnitOfWork:
    """
    Unit of Work pattern for managing database transactions.

    Provides access to all repositories through a single session,
    ensuring that all operations within a unit are committed or
    rolled back together.

    Usage:
        async with UnitOfWork() as uow:
            # All operations use the same session
            user = await uow.users.create_user(email="test@example.com", ...)
            family = await uow.families.create_family(name="Test", owner_user_id=user.id)

            # Commit all changes
            await uow.commit()

        # Or use it without context manager
        uow = UnitOfWork()
        await uow.begin()
        try:
            # ... operations
            await uow.commit()
        except:
            await uow.rollback()
            raise
        finally:
            await uow.close()
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        """
        Initialize Unit of Work.

        Args:
            session: Optional existing session. If not provided,
                     a new session will be created.
        """
        self._session = session
        self._owns_session = session is None

        # Repositories (initialized lazily)
        self._users: Optional[UserRepository] = None
        self._oauth_accounts: Optional[OAuthAccountRepository] = None
        self._refresh_tokens: Optional[RefreshTokenRepository] = None
        self._email_tokens: Optional[EmailVerificationTokenRepository] = None
        self._password_tokens: Optional[PasswordResetTokenRepository] = None
        self._audit_log: Optional[AuditLogRepository] = None

        self._families: Optional[FamilyRepository] = None
        self._family_members: Optional[FamilyMemberRepository] = None
        self._child_access: Optional[ChildAccessRepository] = None
        self._shared_artifacts: Optional[SharedArtifactRepository] = None
        self._invitations: Optional[InvitationRepository] = None

        self._children: Optional[ChildRepository] = None
        self._sessions: Optional[SessionRepository] = None
        self._messages: Optional[MessageRepository] = None
        self._observations: Optional[ObservationRepository] = None


        self._patterns: Optional[PatternRepository] = None
        self._crystals: Optional[CrystalRepository] = None
        self._portrait_sections: Optional[PortraitSectionRepository] = None
        self._intervention_pathways: Optional[InterventionPathwayRepository] = None

        self._darshan: Optional[DarshanRepository] = None

    async def __aenter__(self) -> "UnitOfWork":
        """Enter async context - begin transaction."""
        await self.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context - rollback on exception, close session."""
        if exc_type is not None:
            await self.rollback()
        await self.close()

    async def begin(self) -> None:
        """Begin a new transaction."""
        if self._session is None:
            self._session = AsyncSessionLocal()
            self._owns_session = True

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            await self._session.rollback()

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._session and self._owns_session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> AsyncSession:
        """Get the underlying session."""
        if self._session is None:
            raise RuntimeError("UnitOfWork not started. Call begin() or use as context manager.")
        return self._session

    # =========================================================================
    # AUTH REPOSITORIES
    # =========================================================================

    @property
    def users(self) -> UserRepository:
        if self._users is None:
            self._users = UserRepository(self.session)
        return self._users

    @property
    def oauth_accounts(self) -> OAuthAccountRepository:
        if self._oauth_accounts is None:
            self._oauth_accounts = OAuthAccountRepository(self.session)
        return self._oauth_accounts

    @property
    def refresh_tokens(self) -> RefreshTokenRepository:
        if self._refresh_tokens is None:
            self._refresh_tokens = RefreshTokenRepository(self.session)
        return self._refresh_tokens

    @property
    def email_tokens(self) -> EmailVerificationTokenRepository:
        if self._email_tokens is None:
            self._email_tokens = EmailVerificationTokenRepository(self.session)
        return self._email_tokens

    @property
    def password_tokens(self) -> PasswordResetTokenRepository:
        if self._password_tokens is None:
            self._password_tokens = PasswordResetTokenRepository(self.session)
        return self._password_tokens

    @property
    def audit_log(self) -> AuditLogRepository:
        if self._audit_log is None:
            self._audit_log = AuditLogRepository(self.session)
        return self._audit_log

    # =========================================================================
    # ACCESS REPOSITORIES
    # =========================================================================

    @property
    def families(self) -> FamilyRepository:
        if self._families is None:
            self._families = FamilyRepository(self.session)
        return self._families

    @property
    def family_members(self) -> FamilyMemberRepository:
        if self._family_members is None:
            self._family_members = FamilyMemberRepository(self.session)
        return self._family_members

    @property
    def child_access(self) -> ChildAccessRepository:
        if self._child_access is None:
            self._child_access = ChildAccessRepository(self.session)
        return self._child_access

    @property
    def shared_artifacts(self) -> SharedArtifactRepository:
        if self._shared_artifacts is None:
            self._shared_artifacts = SharedArtifactRepository(self.session)
        return self._shared_artifacts

    @property
    def invitations(self) -> InvitationRepository:
        if self._invitations is None:
            self._invitations = InvitationRepository(self.session)
        return self._invitations

    # =========================================================================
    # CORE REPOSITORIES
    # =========================================================================

    @property
    def children(self) -> ChildRepository:
        if self._children is None:
            self._children = ChildRepository(self.session)
        return self._children

    @property
    def sessions(self) -> SessionRepository:
        if self._sessions is None:
            self._sessions = SessionRepository(self.session)
        return self._sessions

    @property
    def messages(self) -> MessageRepository:
        if self._messages is None:
            self._messages = MessageRepository(self.session)
        return self._messages

    @property
    def observations(self) -> ObservationRepository:
        if self._observations is None:
            self._observations = ObservationRepository(self.session)
        return self._observations


    # =========================================================================
    # SYNTHESIS REPOSITORIES
    # =========================================================================

    @property
    def patterns(self) -> PatternRepository:
        if self._patterns is None:
            self._patterns = PatternRepository(self.session)
        return self._patterns

    @property
    def crystals(self) -> CrystalRepository:
        if self._crystals is None:
            self._crystals = CrystalRepository(self.session)
        return self._crystals

    @property
    def portrait_sections(self) -> PortraitSectionRepository:
        if self._portrait_sections is None:
            self._portrait_sections = PortraitSectionRepository(self.session)
        return self._portrait_sections

    @property
    def intervention_pathways(self) -> InterventionPathwayRepository:
        if self._intervention_pathways is None:
            self._intervention_pathways = InterventionPathwayRepository(self.session)
        return self._intervention_pathways

    # =========================================================================
    # DARSHAN REPOSITORY
    # =========================================================================

    @property
    def darshan(self) -> DarshanRepository:
        if self._darshan is None:
            self._darshan = DarshanRepository(self.session)
        return self._darshan
