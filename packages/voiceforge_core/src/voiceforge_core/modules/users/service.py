from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from voiceforge_core.db.models import User


class UsersService:
    @staticmethod
    def get_by_email(session: Session, email: str) -> User | None:
        return session.scalar(select(User).where(User.email == email.lower()))

    @staticmethod
    def get_by_id(session: Session, user_id: str) -> User | None:
        return session.get(User, user_id)

