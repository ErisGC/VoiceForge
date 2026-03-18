"""Integration tests for FastAPI API routes.

Uses the TestClient fixture from conftest.py, which provides an
authenticated client backed by an in-memory SQLite database.
No external services (PostgreSQL, Redis) are required.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


# -----------------------------------------------------------------------
# Auth routes
# -----------------------------------------------------------------------

class TestAuthRegister:
    def test_register_success(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@voiceforge.dev",
                "display_name": "New User",
                "password": "StrongPass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in_seconds"] > 0

    def test_register_duplicate_email(self, test_client: TestClient) -> None:
        payload = {
            "email": "duplicate@voiceforge.dev",
            "display_name": "First User",
            "password": "StrongPass123!",
        }
        first = test_client.post("/api/v1/auth/register", json=payload)
        assert first.status_code == 201

        second = test_client.post("/api/v1/auth/register", json=payload)
        assert second.status_code == 400

    def test_register_short_password(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@voiceforge.dev",
                "display_name": "Short Pass",
                "password": "123",
            },
        )
        assert response.status_code == 422  # Pydantic validation


class TestAuthLogin:
    def test_login_success(self, test_client: TestClient) -> None:
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@voiceforge.dev",
                "display_name": "Login User",
                "password": "ValidPass123!",
            },
        )
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": "login@voiceforge.dev", "password": "ValidPass123!"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, test_client: TestClient) -> None:
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpw@voiceforge.dev",
                "display_name": "Wrong PW",
                "password": "RealPassword1!",
            },
        )
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@voiceforge.dev", "password": "WrongPass"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@voiceforge.dev", "password": "NoSuchUser1!"},
        )
        assert response.status_code == 401


# -----------------------------------------------------------------------
# Users routes
# -----------------------------------------------------------------------

class TestUsersMe:
    def test_get_current_user(self, test_client: TestClient) -> None:
        response = test_client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@voiceforge.dev"
        assert data["display_name"] == "Test User"


# -----------------------------------------------------------------------
# Voice profiles
# -----------------------------------------------------------------------

class TestVoiceProfiles:
    def _create_profile(self, client: TestClient, name: str = "Test Voice") -> dict:
        response = client.post(
            "/api/v1/voice-profiles",
            json={
                "name": name,
                "description": "A test profile",
                "preferred_backend": "seed_vc",
                "consent_confirmed": True,
                "consent_text": "I consent to voice cloning for testing purposes.",
            },
        )
        assert response.status_code == 201
        return response.json()

    def test_create_profile(self, test_client: TestClient) -> None:
        data = self._create_profile(test_client)
        assert data["name"] == "Test Voice"
        assert data["consent_confirmed"] is True
        assert data["status"] == "draft"
        assert "id" in data

    def test_list_profiles(self, test_client: TestClient) -> None:
        self._create_profile(test_client, "Voice A")
        self._create_profile(test_client, "Voice B")
        response = test_client.get("/api/v1/voice-profiles")
        assert response.status_code == 200
        profiles = response.json()
        assert len(profiles) >= 2
        names = {p["name"] for p in profiles}
        assert "Voice A" in names
        assert "Voice B" in names

    def test_get_profile_by_id(self, test_client: TestClient) -> None:
        created = self._create_profile(test_client, "Get By ID")
        profile_id = created["id"]
        response = test_client.get(f"/api/v1/voice-profiles/{profile_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get By ID"

    def test_get_nonexistent_profile(self, test_client: TestClient) -> None:
        import uuid
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/v1/voice-profiles/{fake_id}")
        assert response.status_code == 404

    def test_create_without_consent_fails(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/voice-profiles",
            json={
                "name": "No Consent",
                "consent_confirmed": False,
                "consent_text": "I do not consent to anything here.",
            },
        )
        assert response.status_code == 400

    def test_list_samples_empty(self, test_client: TestClient) -> None:
        profile = self._create_profile(test_client, "Empty Samples")
        response = test_client.get(
            f"/api/v1/voice-profiles/{profile['id']}/samples"
        )
        assert response.status_code == 200
        assert response.json() == []


# -----------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------

class TestHealthCheck:
    def test_health_endpoint(self, test_client: TestClient) -> None:
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
