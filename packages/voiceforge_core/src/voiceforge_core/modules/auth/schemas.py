from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from voiceforge_core.db.enums import UserRole


class RegisterRequest(BaseModel):
    email: str
    display_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class TokenSubject(BaseModel):
    user_id: UUID
    email: str
    role: UserRole
    exp: int


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    role: UserRole
    created_at: datetime

