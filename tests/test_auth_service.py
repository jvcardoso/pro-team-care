"""
Tests for auth service module
"""

import pytest

from app.infrastructure.services.auth_service import get_password_hash, verify_password


class TestAuthService:
    """Test auth service functionality"""

    def test_password_hashing_and_verification(self):
        """Test password hashing and verification"""
        password = "test_password_123"

        # Test hashing
        hashed = get_password_hash(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20  # BCrypt hashes are long

        # Test verification
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that same password produces different hashes (salt)"""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Should be different due to salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password_handling(self):
        """Test handling of empty passwords"""
        empty_password = ""
        hashed = get_password_hash(empty_password)

        assert verify_password(empty_password, hashed) is True
        assert verify_password("not_empty", hashed) is False
