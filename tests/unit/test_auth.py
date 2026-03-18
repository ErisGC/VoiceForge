"""Unit tests for the authentication service.

Tests password hashing, verification, JWT generation, decoding,
and expiration handling in isolation from the database.
"""
from __future__ import annotations

import time
import uuid

import jwt as pyjwt
import pytest

from voiceforge_core.db.enums import UserRole
from voiceforge_core.db.models import User
from voiceforge_core.modules.auth.service import AuthService

TEST_SECRET = "test-jwt-secret-for-auth-tests"
TEST_EXPIRY_MINUTES = 60


class _FakeUser:
    """Lightweight stand-in for User that exposes the attributes
    AuthService.create_access_token reads (id, email, role)
    without requiring SQLAlchemy instrumentation."""

    def __init__(
        self,
        *,
        email: str = "alice@voiceforge.dev",
        role: UserRole = UserRole.USER,
    ) -> None:
        self.id = uuid.uuid4()
        self.email = email
        self.role = role
        self.is_active = True
        self.display_name = "Alice"


def _make_user(
    *,
    email: str = "alice@voiceforge.dev",
    role: UserRole = UserRole.USER,
) -> _FakeUser:
    """Build a lightweight user object for token tests."""
    return _FakeUser(email=email, role=role)


# -----------------------------------------------------------------------
# Password hashing
# -----------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_produces_non_empty_string(self) -> None:
        hashed = AuthService.hash_password("MySecurePassword123!")
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert "$" in hashed  # salt$digest separator

    def test_verify_correct_password(self) -> None:
        password = "CorrectHorseBatteryStaple"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = AuthService.hash_password("RealPassword")
        assert AuthService.verify_password("WrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        password = "SamePasswordTwice"
        hash_a = AuthService.hash_password(password)
        hash_b = AuthService.hash_password(password)
        assert hash_a != hash_b  # Different salts each time

    def test_verify_with_empty_password(self) -> None:
        hashed = AuthService.hash_password("NonEmpty")
        assert AuthService.verify_password("", hashed) is False


# -----------------------------------------------------------------------
# JWT creation
# -----------------------------------------------------------------------

class TestJwtCreation:
    def test_creates_valid_token(self) -> None:
        user = _make_user()
        token, expires_in = AuthService.create_access_token(
            user, TEST_SECRET, TEST_EXPIRY_MINUTES
        )
        assert isinstance(token, str)
        assert len(token) > 0
        assert expires_in > 0

    def test_token_contains_correct_claims(self) -> None:
        user = _make_user(email="bob@test.dev", role=UserRole.ADMIN)
        token, _ = AuthService.create_access_token(
            user, TEST_SECRET, TEST_EXPIRY_MINUTES
        )
        payload = AuthService.decode_access_token(token, TEST_SECRET)
        assert payload["sub"] == str(user.id)
        assert payload["email"] == "bob@test.dev"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_expires_in_reflects_minutes(self) -> None:
        user = _make_user()
        _, expires_in = AuthService.create_access_token(user, TEST_SECRET, 30)
        assert 0 < expires_in <= 30 * 60


# -----------------------------------------------------------------------
# JWT decoding
# -----------------------------------------------------------------------

class TestJwtDecoding:
    def test_decode_valid_token(self) -> None:
        user = _make_user()
        token, _ = AuthService.create_access_token(
            user, TEST_SECRET, TEST_EXPIRY_MINUTES
        )
        payload = AuthService.decode_access_token(token, TEST_SECRET)
        assert payload["sub"] == str(user.id)

    def test_decode_expired_token_raises(self) -> None:
        user = _make_user()
        # Create a token that expired 1 second ago
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": time.time() - 1,
        }
        expired_token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(pyjwt.ExpiredSignatureError):
            AuthService.decode_access_token(expired_token, TEST_SECRET)

    def test_decode_wrong_secret_raises(self) -> None:
        user = _make_user()
        token, _ = AuthService.create_access_token(
            user, TEST_SECRET, TEST_EXPIRY_MINUTES
        )
        with pytest.raises(pyjwt.InvalidSignatureError):
            AuthService.decode_access_token(token, "wrong-secret")

    def test_decode_malformed_token_raises(self) -> None:
        with pytest.raises(pyjwt.DecodeError):
            AuthService.decode_access_token("not.a.jwt", TEST_SECRET)

    def test_decode_tampered_token_raises(self) -> None:
        user = _make_user()
        token, _ = AuthService.create_access_token(
            user, TEST_SECRET, TEST_EXPIRY_MINUTES
        )
        # Flip a character in the signature
        parts = token.split(".")
        sig = parts[2]
        tampered_sig = sig[:-1] + ("A" if sig[-1] != "A" else "B")
        tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"
        with pytest.raises(pyjwt.InvalidSignatureError):
            AuthService.decode_access_token(tampered_token, TEST_SECRET)
