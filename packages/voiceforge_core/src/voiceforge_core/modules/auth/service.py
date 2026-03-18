from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from voiceforge_core.db.enums import UserRole
from voiceforge_core.db.models import User
from voiceforge_core.modules.users.service import UsersService


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        salt_b64, digest_b64 = stored_hash.split("$", maxsplit=1)
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        expected_digest = base64.urlsafe_b64decode(digest_b64.encode("utf-8"))
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return hmac.compare_digest(candidate, expected_digest)

    @staticmethod
    def create_access_token(user: User, secret: str, expires_in_minutes: int) -> tuple[str, int]:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": expires_at,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token, int((expires_at - datetime.now(timezone.utc)).total_seconds())

    @staticmethod
    def decode_access_token(token: str, secret: str) -> dict:
        return jwt.decode(token, secret, algorithms=["HS256"])

    @staticmethod
    def register_user(session: Session, email: str, display_name: str, password: str) -> User:
        existing = UsersService.get_by_email(session, email)
        if existing:
            raise ValueError("A user with this email already exists.")
        user = User(
            email=email.lower().strip(),
            display_name=display_name.strip(),
            password_hash=AuthService.hash_password(password),
            role=UserRole.USER,
            is_active=True,
        )
        session.add(user)
        session.flush()
        return user

    @staticmethod
    def authenticate(session: Session, email: str, password: str) -> User:
        user = UsersService.get_by_email(session, email)
        if user is None or not AuthService.verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials.")
        if not user.is_active:
            raise ValueError("User account is disabled.")
        return user

