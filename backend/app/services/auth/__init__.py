"""
Authentication Service Package.

Provides JWT-based authentication with:
- Email/password login
- Token refresh with rotation
- Password management
- Email verification

Usage:
    from app.services.auth import AuthService
    from app.db import UnitOfWork

    async with UnitOfWork() as uow:
        auth = AuthService(uow)
        result = await auth.login(email, password)
        await uow.commit()
"""

from app.services.auth.config import AuthSettings, get_auth_settings
from app.services.auth.password import hash_password, verify_password, needs_rehash
from app.services.auth.tokens import (
    TokenService,
    TokenPayload,
    TokenPair,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    get_token_service,
)
from app.services.auth.service import (
    AuthService,
    AuthResult,
    RegistrationResult,
    AuthError,
    InvalidCredentialsError,
    AccountLockedError,
    AccountDisabledError,
    EmailNotVerifiedError,
    EmailAlreadyExistsError,
    TokenReuseError,
)


__all__ = [
    # Config
    "AuthSettings",
    "get_auth_settings",
    # Password
    "hash_password",
    "verify_password",
    "needs_rehash",
    # Tokens
    "TokenService",
    "TokenPayload",
    "TokenPair",
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
    "get_token_service",
    # Service
    "AuthService",
    "AuthResult",
    "RegistrationResult",
    "AuthError",
    "InvalidCredentialsError",
    "AccountLockedError",
    "AccountDisabledError",
    "EmailNotVerifiedError",
    "EmailAlreadyExistsError",
    "TokenReuseError",
]
