"""
Unit tests for JWT Token Service.

Tests token creation, verification, expiration, and security features.
No database required - pure unit tests.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from jose import jwt

from app.services.auth.tokens import (
    TokenService,
    TokenPayload,
    TokenPair,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    get_token_service,
)


class TestAccessTokenCreation:
    """Test access token creation."""

    def test_create_access_token_returns_valid_jwt(self, token_service):
        """create_access_token returns a valid JWT string."""
        user_id = uuid.uuid4()
        token, expires = token_service.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_create_access_token_has_correct_claims(self, token_service):
        """Access token contains correct claims."""
        user_id = uuid.uuid4()
        token, expires = token_service.create_access_token(user_id)

        # Decode without verification to inspect claims
        payload = token_service.decode_token_unverified(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload
        assert payload["iss"] == token_service.settings.token_issuer
        assert payload["aud"] == token_service.settings.token_audience

    def test_create_access_token_default_expiration(self, token_service):
        """Access token uses default expiration from settings."""
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        token, expires = token_service.create_access_token(user_id)

        expected_expires = now + token_service.settings.access_token_expires
        # Allow 5 seconds tolerance
        assert abs((expires - expected_expires).total_seconds()) < 5

    def test_create_access_token_custom_expiration(self, token_service):
        """Access token respects custom expiration."""
        user_id = uuid.uuid4()
        custom_delta = timedelta(minutes=5)
        now = datetime.now(timezone.utc)

        token, expires = token_service.create_access_token(
            user_id, expires_delta=custom_delta
        )

        expected_expires = now + custom_delta
        assert abs((expires - expected_expires).total_seconds()) < 5

    def test_create_access_token_unique_jti(self, token_service):
        """Each access token has unique jti."""
        user_id = uuid.uuid4()

        token1, _ = token_service.create_access_token(user_id)
        token2, _ = token_service.create_access_token(user_id)

        payload1 = token_service.decode_token_unverified(token1)
        payload2 = token_service.decode_token_unverified(token2)

        assert payload1["jti"] != payload2["jti"]


class TestRefreshTokenCreation:
    """Test refresh token creation."""

    def test_create_refresh_token_returns_tuple(self, token_service):
        """create_refresh_token returns (token, expires, family, hash)."""
        user_id = uuid.uuid4()
        result = token_service.create_refresh_token(user_id)

        assert len(result) == 4
        token, expires, family, token_hash = result

        assert isinstance(token, str)
        assert isinstance(expires, datetime)
        assert isinstance(family, uuid.UUID)
        assert isinstance(token_hash, str)

    def test_create_refresh_token_has_family_claim(self, token_service):
        """Refresh token contains family claim."""
        user_id = uuid.uuid4()
        token, expires, family, _ = token_service.create_refresh_token(user_id)

        payload = token_service.decode_token_unverified(token)

        assert payload["type"] == "refresh"
        assert payload["family"] == str(family)

    def test_create_refresh_token_new_family(self, token_service):
        """New family is created when not provided."""
        user_id = uuid.uuid4()

        _, _, family1, _ = token_service.create_refresh_token(user_id)
        _, _, family2, _ = token_service.create_refresh_token(user_id)

        assert family1 != family2

    def test_create_refresh_token_existing_family(self, token_service):
        """Existing family is used when provided."""
        user_id = uuid.uuid4()
        existing_family = uuid.uuid4()

        _, _, family, _ = token_service.create_refresh_token(
            user_id, token_family=existing_family
        )

        assert family == existing_family

    def test_create_refresh_token_hash_is_sha256(self, token_service):
        """Token hash is SHA-256 (64 hex characters)."""
        user_id = uuid.uuid4()
        _, _, _, token_hash = token_service.create_refresh_token(user_id)

        assert len(token_hash) == 64
        assert all(c in "0123456789abcdef" for c in token_hash)


class TestTokenPairCreation:
    """Test token pair creation."""

    def test_create_token_pair_returns_tuple(self, token_service):
        """create_token_pair returns (TokenPair, family, hash)."""
        user_id = uuid.uuid4()
        result = token_service.create_token_pair(user_id)

        assert len(result) == 3
        token_pair, family, token_hash = result

        assert isinstance(token_pair, TokenPair)
        assert isinstance(family, uuid.UUID)
        assert isinstance(token_hash, str)

    def test_create_token_pair_has_both_tokens(self, token_service):
        """TokenPair contains both access and refresh tokens."""
        user_id = uuid.uuid4()
        token_pair, _, _ = token_service.create_token_pair(user_id)

        assert token_pair.access_token is not None
        assert token_pair.refresh_token is not None
        assert token_pair.access_token != token_pair.refresh_token

    def test_create_token_pair_has_expirations(self, token_service):
        """TokenPair contains expiration times."""
        user_id = uuid.uuid4()
        token_pair, _, _ = token_service.create_token_pair(user_id)

        assert token_pair.access_token_expires is not None
        assert token_pair.refresh_token_expires is not None
        # Refresh should expire later than access
        assert token_pair.refresh_token_expires > token_pair.access_token_expires

    def test_create_token_pair_token_type(self, token_service):
        """TokenPair has bearer token type."""
        user_id = uuid.uuid4()
        token_pair, _, _ = token_service.create_token_pair(user_id)

        assert token_pair.token_type == "bearer"


class TestAccessTokenVerification:
    """Test access token verification."""

    def test_verify_access_token_valid(self, token_service):
        """Valid access token verifies successfully."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(user_id)

        payload = token_service.verify_access_token(token)

        assert payload.sub == str(user_id)
        assert payload.type == "access"

    def test_verify_access_token_returns_payload(self, token_service):
        """verify_access_token returns TokenPayload."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(user_id)

        payload = token_service.verify_access_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == str(user_id)
        assert payload.type == "access"
        assert payload.jti is not None
        assert payload.iss == token_service.settings.token_issuer
        assert payload.aud == token_service.settings.token_audience

    def test_verify_access_token_expired(self, token_service):
        """Expired access token raises TokenExpiredError."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(
            user_id, expires_delta=timedelta(seconds=-10)
        )

        with pytest.raises(TokenExpiredError):
            token_service.verify_access_token(token)

    def test_verify_access_token_wrong_type(self, token_service):
        """Refresh token fails access verification."""
        user_id = uuid.uuid4()
        token, _, _, _ = token_service.create_refresh_token(user_id)

        with pytest.raises(TokenInvalidError) as exc_info:
            token_service.verify_access_token(token)

        assert "Expected access token" in str(exc_info.value)

    def test_verify_access_token_invalid_signature(self, token_service):
        """Token with invalid signature raises TokenInvalidError."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(user_id)

        # Tamper with the token
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(TokenInvalidError):
            token_service.verify_access_token(tampered)

    def test_verify_access_token_malformed(self, token_service):
        """Malformed token raises TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            token_service.verify_access_token("not.a.valid.jwt")

    def test_verify_access_token_wrong_secret(self, token_service):
        """Token created with different secret fails verification."""
        user_id = uuid.uuid4()

        # Create token with different secret
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iss": token_service.settings.token_issuer,
            "aud": token_service.settings.token_audience,
        }
        bad_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with pytest.raises(TokenInvalidError):
            token_service.verify_access_token(bad_token)


class TestRefreshTokenVerification:
    """Test refresh token verification."""

    def test_verify_refresh_token_valid(self, token_service):
        """Valid refresh token verifies successfully."""
        user_id = uuid.uuid4()
        token, _, family, _ = token_service.create_refresh_token(user_id)

        payload = token_service.verify_refresh_token(token)

        assert payload.sub == str(user_id)
        assert payload.type == "refresh"
        assert payload.family == str(family)

    def test_verify_refresh_token_expired(self, token_service):
        """Expired refresh token raises TokenExpiredError."""
        user_id = uuid.uuid4()
        token, _, _, _ = token_service.create_refresh_token(
            user_id, expires_delta=timedelta(seconds=-10)
        )

        with pytest.raises(TokenExpiredError):
            token_service.verify_refresh_token(token)

    def test_verify_refresh_token_wrong_type(self, token_service):
        """Access token fails refresh verification."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(user_id)

        with pytest.raises(TokenInvalidError) as exc_info:
            token_service.verify_refresh_token(token)

        assert "Expected refresh token" in str(exc_info.value)


class TestTokenHashing:
    """Test token hashing functionality."""

    def test_get_token_hash_returns_sha256(self, token_service):
        """get_token_hash returns SHA-256 hash."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(user_id)

        hash_value = token_service.get_token_hash(token)

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_get_token_hash_deterministic(self, token_service):
        """Same token always produces same hash."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(user_id)

        hash1 = token_service.get_token_hash(token)
        hash2 = token_service.get_token_hash(token)

        assert hash1 == hash2

    def test_different_tokens_different_hashes(self, token_service):
        """Different tokens produce different hashes."""
        user_id = uuid.uuid4()
        token1, _ = token_service.create_access_token(user_id)
        token2, _ = token_service.create_access_token(user_id)

        hash1 = token_service.get_token_hash(token1)
        hash2 = token_service.get_token_hash(token2)

        assert hash1 != hash2


class TestVerificationTokenGeneration:
    """Test verification/reset token generation."""

    def test_generate_verification_token_returns_tuple(self, token_service):
        """generate_verification_token returns (token, hash) tuple."""
        result = token_service.generate_verification_token()

        assert len(result) == 2
        token, token_hash = result

        assert isinstance(token, str)
        assert isinstance(token_hash, str)

    def test_generate_verification_token_unique(self, token_service):
        """Each generated token is unique."""
        tokens = [token_service.generate_verification_token()[0] for _ in range(10)]

        assert len(set(tokens)) == 10

    def test_generate_verification_token_hash_matches(self, token_service):
        """Token hash matches when computed manually."""
        import hashlib

        token, token_hash = token_service.generate_verification_token()
        computed_hash = hashlib.sha256(token.encode()).hexdigest()

        assert token_hash == computed_hash

    def test_generate_verification_token_is_url_safe(self, token_service):
        """Generated token is URL-safe."""
        token, _ = token_service.generate_verification_token()

        # URL-safe base64 characters
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', token)


class TestDecodeUnverified:
    """Test unverified token decoding."""

    def test_decode_token_unverified_valid(self, token_service):
        """decode_token_unverified works on valid token."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(user_id)

        payload = token_service.decode_token_unverified(token)

        assert payload["sub"] == str(user_id)

    def test_decode_token_unverified_expired(self, token_service):
        """decode_token_unverified works on expired token."""
        user_id = uuid.uuid4()
        token, _ = token_service.create_access_token(
            user_id, expires_delta=timedelta(seconds=-10)
        )

        # Should not raise despite expiration
        payload = token_service.decode_token_unverified(token)

        assert payload["sub"] == str(user_id)


class TestTokenServiceSingleton:
    """Test token service singleton."""

    def test_get_token_service_returns_same_instance(self):
        """get_token_service returns the same instance."""
        # Reset singleton for test
        import app.services.auth.tokens as tokens_module
        tokens_module._token_service = None

        service1 = get_token_service()
        service2 = get_token_service()

        assert service1 is service2

    def test_get_token_service_is_token_service(self):
        """get_token_service returns TokenService instance."""
        service = get_token_service()

        assert isinstance(service, TokenService)
