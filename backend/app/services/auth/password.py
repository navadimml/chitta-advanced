"""
Password Hashing Utilities.

Uses bcrypt for secure password hashing.
"""

from passlib.context import CryptContext

from app.services.auth.config import get_auth_settings

# Password hashing context
_pwd_context: CryptContext = None


def _get_pwd_context() -> CryptContext:
    """Get or create password context."""
    global _pwd_context
    if _pwd_context is None:
        settings = get_auth_settings()
        _pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=settings.password_hash_rounds
        )
    return _pwd_context


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return _get_pwd_context().hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against

    Returns:
        True if password matches
    """
    return _get_pwd_context().verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if password hash needs to be rehashed.

    This happens when the hashing parameters change
    (e.g., increased bcrypt rounds).

    Args:
        hashed_password: Existing hash

    Returns:
        True if should rehash
    """
    return _get_pwd_context().needs_update(hashed_password)
