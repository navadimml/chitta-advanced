"""
Authentication Configuration.

Centralized configuration for JWT tokens, password hashing,
and other auth-related settings.

All values can be overridden via environment variables.
"""

import os
from datetime import timedelta
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """Authentication settings loaded from environment."""

    # JWT Configuration
    jwt_secret_key: str = "dev-secret-key-change-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"

    # Access token (short-lived)
    access_token_expire_minutes: int = 30

    # Refresh token (long-lived)
    refresh_token_expire_days: int = 30

    # Password hashing
    password_hash_rounds: int = 12  # bcrypt rounds

    # Account security
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30

    # Token settings
    token_issuer: str = "chitta"
    token_audience: str = "chitta-api"

    # Email verification
    email_verification_expire_hours: int = 24

    # Password reset
    password_reset_expire_hours: int = 1

    # OAuth providers (optional)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    apple_client_id: Optional[str] = None
    apple_team_id: Optional[str] = None
    apple_key_id: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="",  # No prefix, use exact names
        env_file=".env",
        extra="ignore"
    )

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.refresh_token_expire_days)

    @property
    def email_verification_expires(self) -> timedelta:
        return timedelta(hours=self.email_verification_expire_hours)

    @property
    def password_reset_expires(self) -> timedelta:
        return timedelta(hours=self.password_reset_expire_hours)

    @property
    def lockout_duration(self) -> timedelta:
        return timedelta(minutes=self.lockout_duration_minutes)


# Global settings instance
_settings: Optional[AuthSettings] = None


def get_auth_settings() -> AuthSettings:
    """Get auth settings singleton."""
    global _settings
    if _settings is None:
        _settings = AuthSettings()
    return _settings


# Convenience accessors
def get_jwt_secret() -> str:
    return get_auth_settings().jwt_secret_key


def get_jwt_algorithm() -> str:
    return get_auth_settings().jwt_algorithm
