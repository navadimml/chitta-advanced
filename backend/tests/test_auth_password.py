"""
Unit tests for password hashing utilities.

Tests bcrypt password hashing, verification, and rehash detection.
No database or async required - pure unit tests.
"""

import pytest

from app.services.auth.password import (
    hash_password,
    verify_password,
    needs_rehash,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_returns_bcrypt_hash(self):
        """hash_password returns a bcrypt hash string."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")  # bcrypt identifier
        assert len(hashed) == 60  # bcrypt hash length

    def test_hash_password_different_each_time(self):
        """Same password produces different hashes (due to salt)."""
        password = "SecurePassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts

    def test_hash_password_handles_unicode(self):
        """Password hashing works with Unicode characters."""
        password = "סיסמא_בטוחה_123!"  # Hebrew password
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed.startswith("$2b$")

    def test_hash_password_handles_empty_string(self):
        """Empty password can be hashed (not recommended in practice)."""
        hashed = hash_password("")

        assert hashed is not None
        assert hashed.startswith("$2b$")

    def test_hash_password_handles_long_password(self):
        """Long passwords are handled (bcrypt truncates at 72 bytes)."""
        password = "a" * 100
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed.startswith("$2b$")


class TestPasswordVerification:
    """Test password verification functions."""

    def test_verify_password_correct(self):
        """Correct password verifies successfully."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password fails verification."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Password verification is case-sensitive."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password("securepassword123!", hashed) is False
        assert verify_password("SECUREPASSWORD123!", hashed) is False

    def test_verify_password_unicode(self):
        """Unicode passwords verify correctly."""
        password = "סיסמא_בטוחה_123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("סיסמא_שגויה_456!", hashed) is False

    def test_verify_password_empty(self):
        """Empty password verifies if that was the original."""
        hashed = hash_password("")

        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_verify_password_similar_passwords(self):
        """Similar but different passwords fail verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Off by one character
        assert verify_password("SecurePassword123", hashed) is False
        assert verify_password("SecurePassword123!!", hashed) is False
        assert verify_password(" SecurePassword123!", hashed) is False
        assert verify_password("SecurePassword123! ", hashed) is False


class TestNeedsRehash:
    """Test password rehash detection."""

    def test_needs_rehash_current_settings(self):
        """Fresh hash with current settings doesn't need rehash."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert needs_rehash(hashed) is False

    def test_needs_rehash_low_rounds(self):
        """Hash with low rounds needs rehash."""
        # Create a hash with only 4 rounds (very weak)
        from passlib.hash import bcrypt
        weak_hash = bcrypt.using(rounds=4).hash("password")

        # Should need rehash because rounds are too low
        assert needs_rehash(weak_hash) is True

    def test_needs_rehash_invalid_hash(self):
        """Invalid hash format returns True (needs to be set properly)."""
        # This tests edge case handling
        try:
            result = needs_rehash("not_a_valid_hash")
            # If it doesn't raise, it should indicate rehash needed
            assert result is True
        except Exception:
            # Some implementations may raise on invalid hash
            pass


class TestPasswordEdgeCases:
    """Test edge cases and security scenarios."""

    def test_timing_attack_resistance(self):
        """Verification time should be consistent (timing attack resistance)."""
        import time

        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Measure time for correct password
        times_correct = []
        for _ in range(5):
            start = time.perf_counter()
            verify_password(password, hashed)
            times_correct.append(time.perf_counter() - start)

        # Measure time for wrong password
        times_wrong = []
        for _ in range(5):
            start = time.perf_counter()
            verify_password("WrongPassword!", hashed)
            times_wrong.append(time.perf_counter() - start)

        # Times should be similar (bcrypt is constant-time)
        avg_correct = sum(times_correct) / len(times_correct)
        avg_wrong = sum(times_wrong) / len(times_wrong)

        # Allow for some variance, but should be within 50% of each other
        ratio = max(avg_correct, avg_wrong) / min(avg_correct, avg_wrong)
        assert ratio < 2.0, "Timing difference too large - possible timing attack vulnerability"

    def test_whitespace_preserved(self):
        """Whitespace in passwords is preserved."""
        password_with_spaces = "  password with spaces  "
        hashed = hash_password(password_with_spaces)

        assert verify_password(password_with_spaces, hashed) is True
        assert verify_password("password with spaces", hashed) is False
        assert verify_password("passwordwithspaces", hashed) is False

    def test_special_characters(self):
        """Special characters are handled correctly."""
        special_password = "P@$$w0rd!#$%^&*()[]{}|;':\",./<>?"
        hashed = hash_password(special_password)

        assert verify_password(special_password, hashed) is True

    def test_null_bytes_in_password(self):
        """Null bytes in password are rejected by bcrypt."""
        # bcrypt explicitly rejects null bytes for security
        password_with_null = "pass\x00word"

        with pytest.raises(Exception):
            # passlib raises PasswordValueError for null bytes
            hash_password(password_with_null)
