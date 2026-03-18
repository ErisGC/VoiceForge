"""Root conftest for VoiceForge test suite.

Provides shared fixtures for database sessions, FastAPI test client,
and authenticated user helpers. All tests run against an in-memory
SQLite database with no external service dependencies.
"""
from __future__ import annotations

import sys
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# Add services/api to sys.path so `import app` works from the test root
_API_DIR = str(Path(__file__).resolve().parent.parent / "services" / "api")
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from voiceforge_core.db.base import Base
from voiceforge_core.db.enums import SubscriptionPlan, SubscriptionStatus, UserRole
from voiceforge_core.db.models import Subscription, User
from voiceforge_core.modules.auth.service import AuthService

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

SQLITE_URL = "sqlite://"
TEST_JWT_SECRET = "test-secret-key-for-voiceforge-tests"
TEST_JWT_EXPIRY_MINUTES = 60


@pytest.fixture()
def db_engine() -> Generator[Engine, None, None]:
    """Create a fresh in-memory SQLite engine per test.

    Uses StaticPool and check_same_thread=False so that the FastAPI
    TestClient (which runs in a worker thread) can share the same
    in-memory database as the test thread.

    Tables are created fresh for each test for full isolation.
    """
    engine = create_engine(
        SQLITE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Provide a database session for each test."""
    session = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def test_user(db_session: Session) -> User:
    """Create and return a persisted test user."""
    user = User(
        id=uuid.uuid4(),
        email="testuser@voiceforge.dev",
        display_name="Test User",
        password_hash=AuthService.hash_password("SecurePass123!"),
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(autouse=True)
def _test_user_subscription(db_session: Session, test_user: User) -> None:
    """Give the test user an Unlimited subscription so quota checks pass in integration tests."""
    from datetime import datetime, timedelta, timezone

    sub = Subscription(
        user_id=test_user.id,
        plan=SubscriptionPlan.UNLIMITED,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    db_session.commit()


@pytest.fixture()
def auth_token(test_user: User) -> str:
    """Generate a valid JWT for the test user."""
    token, _ = AuthService.create_access_token(
        test_user, TEST_JWT_SECRET, TEST_JWT_EXPIRY_MINUTES
    )
    return token


@pytest.fixture()
def test_client(db_engine: Engine, test_user: User) -> Generator:
    """Create a FastAPI TestClient with dependency overrides.

    Overrides the database session and settings so the API runs
    entirely against the in-memory SQLite database. Each API request
    gets its own session from the shared engine.
    """
    from fastapi.testclient import TestClient

    from app.dependencies import get_current_user, get_db
    from app.main import app
    from app.settings import Settings, get_settings

    _SessionFactory = sessionmaker(
        bind=db_engine, autoflush=False, autocommit=False,
    )

    settings = Settings(
        database_url=SQLITE_URL,
        redis_url="redis://localhost:6379/0",
        jwt_secret=TEST_JWT_SECRET,
        access_token_exp_minutes=TEST_JWT_EXPIRY_MINUTES,
        rate_limit_per_minute=1000,
    )

    def _override_db() -> Generator[Session, None, None]:
        session = _SessionFactory()
        try:
            yield session
        finally:
            session.close()

    def _override_current_user() -> User:
        return test_user

    def _override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_settings] = _override_settings

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
