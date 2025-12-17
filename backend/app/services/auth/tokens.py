"""
JWT Token Service.

Handles creation and verification of:
- Access tokens (short-lived, for API authentication)
- Refresh tokens (long-lived, for obtaining new access tokens)

Implements secure token rotation with family tracking.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass

from jose import jwt, JWTError, ExpiredSignatureError

from app.services.auth.config import get_auth_settings


@dataclass
class TokenPayload:
    """Decoded token payload."""
    sub: str  # Subject (user ID)
    exp: datetime  # Expiration
    iat: datetime  # Issued at
    jti: str  # JWT ID (unique identifier)
    type: str  # 'access' or 'refresh'
    iss: str  # Issuer
    aud: str  # Audience
    family: Optional[str] = None  # Token family (for refresh tokens)


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    access_token_expires: datetime
    refresh_token_expires: datetime
    token_type: str = "bearer"


class TokenError(Exception):
    """Base exception for token errors."""
    pass


class TokenExpiredError(TokenError):
    """Token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Token is invalid (bad signature, malformed, etc.)."""
    pass


class TokenService:
    """
    Service for JWT token operations.

    Usage:
        service = TokenService()

        # Create tokens
        tokens = service.create_token_pair(user_id)

        # Verify access token
        payload = service.verify_access_token(tokens.access_token)

        # Refresh tokens
        new_tokens, old_family = service.create_refreshed_tokens(
            tokens.refresh_token
        )
    """

    def __init__(self):
        self.settings = get_auth_settings()

    def create_access_token(
        self,
        user_id: uuid.UUID,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, datetime]:
        """
        Create an access token.

        Args:
            user_id: User's UUID
            expires_delta: Optional custom expiration

        Returns:
            Tuple of (token_string, expiration_datetime)
        """
        now = datetime.now(timezone.utc)
        expires = now + (expires_delta or self.settings.access_token_expires)

        payload = {
            "sub": str(user_id),
            "exp": expires,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iss": self.settings.token_issuer,
            "aud": self.settings.token_audience,
        }

        token = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )

        return token, expires

    def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token_family: Optional[uuid.UUID] = None,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, datetime, uuid.UUID, str]:
        """
        Create a refresh token.

        Args:
            user_id: User's UUID
            token_family: Family ID for rotation tracking (new if None)
            expires_delta: Optional custom expiration

        Returns:
            Tuple of (token_string, expiration, family_id, token_hash)
        """
        now = datetime.now(timezone.utc)
        expires = now + (expires_delta or self.settings.refresh_token_expires)

        # Generate or use existing family
        family = token_family or uuid.uuid4()

        # Generate unique token ID
        jti = str(uuid.uuid4())

        payload = {
            "sub": str(user_id),
            "exp": expires,
            "iat": now,
            "jti": jti,
            "type": "refresh",
            "iss": self.settings.token_issuer,
            "aud": self.settings.token_audience,
            "family": str(family),
        }

        token = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )

        # Hash for storage (we store hash, not actual token)
        token_hash = self._hash_token(token)

        return token, expires, family, token_hash

    def create_token_pair(
        self,
        user_id: uuid.UUID,
        token_family: Optional[uuid.UUID] = None
    ) -> Tuple[TokenPair, uuid.UUID, str]:
        """
        Create both access and refresh tokens.

        Args:
            user_id: User's UUID
            token_family: Optional family for refresh token

        Returns:
            Tuple of (TokenPair, family_id, refresh_token_hash)
        """
        access_token, access_expires = self.create_access_token(user_id)
        refresh_token, refresh_expires, family, token_hash = self.create_refresh_token(
            user_id, token_family
        )

        token_pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires=access_expires,
            refresh_token_expires=refresh_expires,
        )

        return token_pair, family, token_hash

    def verify_access_token(self, token: str) -> TokenPayload:
        """
        Verify an access token.

        Args:
            token: JWT token string

        Returns:
            Decoded TokenPayload

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
        """
        return self._verify_token(token, expected_type="access")

    def verify_refresh_token(self, token: str) -> TokenPayload:
        """
        Verify a refresh token.

        Args:
            token: JWT token string

        Returns:
            Decoded TokenPayload

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
        """
        return self._verify_token(token, expected_type="refresh")

    def _verify_token(self, token: str, expected_type: str) -> TokenPayload:
        """
        Internal token verification.

        Args:
            token: JWT token string
            expected_type: 'access' or 'refresh'

        Returns:
            Decoded TokenPayload

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                audience=self.settings.token_audience,
                issuer=self.settings.token_issuer,
            )

            # Verify token type
            if payload.get("type") != expected_type:
                raise TokenInvalidError(f"Expected {expected_type} token")

            return TokenPayload(
                sub=payload["sub"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=payload["jti"],
                type=payload["type"],
                iss=payload["iss"],
                aud=payload["aud"],
                family=payload.get("family"),
            )

        except ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except JWTError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")

    def decode_token_unverified(self, token: str) -> dict:
        """
        Decode token without verification.

        Useful for extracting claims from expired tokens.

        Args:
            token: JWT token string

        Returns:
            Raw payload dict
        """
        return jwt.decode(
            token,
            self.settings.jwt_secret_key,
            algorithms=[self.settings.jwt_algorithm],
            options={"verify_signature": False, "verify_exp": False}
        )

    def get_token_hash(self, token: str) -> str:
        """
        Get hash of a token for storage comparison.

        Args:
            token: JWT token string

        Returns:
            SHA-256 hash
        """
        return self._hash_token(token)

    def _hash_token(self, token: str) -> str:
        """Hash a token using SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_verification_token(self) -> Tuple[str, str]:
        """
        Generate a random token for email verification or password reset.

        Returns:
            Tuple of (plain_token, token_hash)
        """
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash


# Global instance
_token_service: Optional[TokenService] = None


def get_token_service() -> TokenService:
    """Get token service singleton."""
    global _token_service
    if _token_service is None:
        _token_service = TokenService()
    return _token_service
