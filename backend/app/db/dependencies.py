"""
FastAPI Dependencies for Database Access.

Provides dependency injection for:
- UnitOfWork (main database access)
- Current user authentication
- Permission checks
- Child access validation

Usage in endpoints:
    @router.get("/children/{child_id}")
    async def get_child(
        child_id: UUID,
        uow: UnitOfWork = Depends(get_uow),
        current_user: User = Depends(get_current_user),
    ):
        ...
"""

import uuid
from typing import Optional, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.repositories import UnitOfWork
from app.db.models_auth import User
from app.db.models_core import Child

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    """
    Dependency that provides a UnitOfWork instance.

    Automatically commits on success, rolls back on exception.

    Usage:
        @router.post("/users")
        async def create_user(uow: UnitOfWork = Depends(get_uow)):
            user = await uow.users.create_user(...)
            await uow.commit()
            return user
    """
    uow = UnitOfWork()
    await uow.begin()
    try:
        yield uow
        # Note: We don't auto-commit here - let the endpoint decide
        # This allows for explicit control over transactions
    except Exception:
        await uow.rollback()
        raise
    finally:
        await uow.close()


async def get_uow_autocommit() -> AsyncGenerator[UnitOfWork, None]:
    """
    Dependency that auto-commits on success.

    Use this for simple endpoints where you always want to commit
    if no exception occurs.

    Usage:
        @router.post("/users")
        async def create_user(uow: UnitOfWork = Depends(get_uow_autocommit)):
            user = await uow.users.create_user(...)
            # Auto-commits when endpoint returns successfully
            return user
    """
    uow = UnitOfWork()
    await uow.begin()
    try:
        yield uow
        await uow.commit()
    except Exception:
        await uow.rollback()
        raise
    finally:
        await uow.close()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    uow: UnitOfWork = Depends(get_uow),
) -> Optional[User]:
    """
    Get current user from JWT token, or None if not authenticated.

    Use this for endpoints that work differently for authenticated
    vs anonymous users.
    """
    if not credentials:
        return None

    try:
        from app.services.auth import get_token_service, TokenExpiredError, TokenInvalidError

        token_service = get_token_service()

        # Verify access token
        payload = token_service.verify_access_token(credentials.credentials)

        # Get user from database
        user = await uow.users.get_by_id(uuid.UUID(payload.sub))
        return user

    except (TokenExpiredError, TokenInvalidError):
        return None
    except Exception:
        return None


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """
    Get current authenticated user, or raise 401.

    Use this for endpoints that require authentication.

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify they are active.

    Alias for get_current_user with explicit naming.
    """
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify they are an admin.

    Usage:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            admin: User = Depends(get_current_admin_user)
        ):
            ...
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


class ChildAccessChecker:
    """
    Dependency class for checking child access permissions.

    Usage:
        @router.get("/children/{child_id}")
        async def get_child(
            child_id: UUID,
            access: ChildAccessChecker = Depends(ChildAccessChecker()),
        ):
            child = await access.get_child_or_403(child_id)
            return child
    """

    def __init__(
        self,
        require_chat: bool = False,
        require_observations: bool = False,
        require_clinical: bool = False,
        require_manage: bool = False,
    ):
        """
        Configure required permissions.

        Args:
            require_chat: User must be able to chat with Chitta about child
            require_observations: User must be able to add observations
            require_clinical: User must be able to add clinical notes
            require_manage: User must be able to manage access (owner/parent only)
        """
        self.require_chat = require_chat
        self.require_observations = require_observations
        self.require_clinical = require_clinical
        self.require_manage = require_manage

    async def __call__(
        self,
        uow: UnitOfWork = Depends(get_uow),
        current_user: User = Depends(get_current_user),
    ) -> "ChildAccessChecker":
        """Store dependencies for later use."""
        self.uow = uow
        self.current_user = current_user
        return self

    async def get_child_or_403(self, child_id: uuid.UUID) -> Child:
        """
        Get child if user has access, raise 403 otherwise.

        Also checks specific permission requirements.
        """
        # Check basic access
        access_info = await self.uow.children.get_user_access_type(
            self.current_user.id,
            child_id
        )

        if not access_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this child",
            )

        permissions = access_info.get("permissions", {})

        # Check specific permissions
        if self.require_chat and not permissions.get("can_chat"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to chat about this child",
            )

        if self.require_observations and not permissions.get("can_add_observations"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add observations",
            )

        if self.require_clinical and not permissions.get("can_add_clinical_notes"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add clinical notes",
            )

        if self.require_manage and not permissions.get("can_manage_access"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage access",
            )

        # Get and return the child
        child = await self.uow.children.get_by_id(child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found",
            )

        return child

    async def check_access(self, child_id: uuid.UUID) -> dict:
        """
        Check access and return permissions dict.

        Returns the full access info without raising exceptions.
        """
        return await self.uow.children.get_user_access_type(
            self.current_user.id,
            child_id
        )


class FamilyAccessChecker:
    """
    Dependency class for checking family access permissions.

    Usage:
        @router.get("/families/{family_id}")
        async def get_family(
            family_id: UUID,
            access: FamilyAccessChecker = Depends(FamilyAccessChecker()),
        ):
            family = await access.get_family_or_403(family_id)
            return family
    """

    def __init__(
        self,
        require_owner: bool = False,
        require_parent: bool = False,
    ):
        """
        Configure required role.

        Args:
            require_owner: User must be family owner
            require_parent: User must be owner or parent
        """
        self.require_owner = require_owner
        self.require_parent = require_parent

    async def __call__(
        self,
        uow: UnitOfWork = Depends(get_uow),
        current_user: User = Depends(get_current_user),
    ) -> "FamilyAccessChecker":
        """Store dependencies for later use."""
        self.uow = uow
        self.current_user = current_user
        return self

    async def get_family_or_403(self, family_id: uuid.UUID):
        """
        Get family if user is a member, raise 403 otherwise.
        """
        membership = await self.uow.family_members.get_membership(
            self.current_user.id,
            family_id
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this family",
            )

        if self.require_owner and membership.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family owners can perform this action",
            )

        if self.require_parent and membership.role not in ["owner", "parent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only parents can perform this action",
            )

        family = await self.uow.families.get_by_id(family_id)
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found",
            )

        return family

    async def get_role(self, family_id: uuid.UUID) -> Optional[str]:
        """Get user's role in family."""
        return await self.uow.family_members.get_role(
            self.current_user.id,
            family_id
        )


# Convenience dependency instances
require_child_chat = ChildAccessChecker(require_chat=True)
require_child_observations = ChildAccessChecker(require_observations=True)
require_child_clinical = ChildAccessChecker(require_clinical=True)
require_child_manage = ChildAccessChecker(require_manage=True)

require_family_owner = FamilyAccessChecker(require_owner=True)
require_family_parent = FamilyAccessChecker(require_parent=True)


class RequireAuth:
    """
    Simple authentication requirement for string-based family_ids.

    This dependency:
    1. Requires user to be authenticated
    2. Logs access to the family
    3. Stores user for downstream use

    Use this for endpoints that use string family_ids (not yet migrated to DB).
    For UUID-based families, use FamilyAccessChecker instead.

    Usage:
        @router.get("/family/{family_id}/data")
        async def get_data(
            family_id: str,
            auth: RequireAuth = Depends(RequireAuth()),
        ):
            # auth.user is the authenticated user
            # auth.family_id is set after calling verify_access
            ...
    """

    def __init__(self, log_access: bool = True):
        """
        Args:
            log_access: Whether to log family access (default True)
        """
        self.log_access = log_access
        self.user: Optional[User] = None
        self.family_id: Optional[str] = None

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> "RequireAuth":
        """Store authenticated user."""
        self.user = current_user
        return self

    def verify_access(self, family_id: str) -> User:
        """
        Verify user has access to family and log the access.

        For now, any authenticated user can access any family.
        This can be extended later to check actual permissions
        once families are migrated to the database.

        Args:
            family_id: String-based family identifier

        Returns:
            The authenticated user

        Raises:
            HTTPException: If not authenticated
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        self.family_id = family_id

        if self.log_access:
            logger.info(f"🔐 User {self.user.email} accessing family {family_id}")

        # TODO: Add actual family-level permission check once families
        # are migrated to the database. For now, any authenticated user
        # can access any family.
        #
        # Future implementation:
        # 1. Look up family in DB by string ID or create mapping
        # 2. Check if user has FamilyMember or ChildAccess relationship
        # 3. Raise 403 if no access

        return self.user


# Simple auth requirement instance
require_auth = RequireAuth()
