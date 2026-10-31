from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routers import profile as profile_router
from backend.app.security import CurrentUser
from backend.app.services import profile as profile_service


@pytest.fixture
def client(monkeypatch):
    account = SimpleNamespace(
        user_id=7,
        name="Ім'я",
        nickname="nick",
        email="original@example.com",
        role="user",
        password_hash="old-hash",
        token_version=0,
        email_reminders_enabled=False,
        message_style="formal",
    )
    db = Mock()
    monkeypatch.setattr(profile_service, "get_user", lambda session, user_id: account)
    def public_result(session, user):
        return {
            "user_id": user.user_id,
            "name": user.name,
            "nickname": user.nickname,
            "email": user.email,
            "has_avatar": False,
            "avatar_version": None,
            "email_reminders_enabled": user.email_reminders_enabled,
            "message_style": user.message_style,
        }
    monkeypatch.setattr(profile_service, "profile_result", public_result)
    monkeypatch.setattr(profile_router, "profile_result", public_result)
    app = FastAPI()
    app.include_router(profile_router.router, prefix="/api/v1")
    app.dependency_overrides[profile_router.get_current_user] = lambda: CurrentUser(
        user_id=7, role="user"
    )
    app.dependency_overrides[profile_router._db_session] = lambda: db
    with TestClient(app) as http:
        yield http, account, db


def test_profile_endpoints_return_owner_fields_without_mentor_code(client):
    http, _, _ = client
    response = http.get("/api/v1/profile")
    assert response.status_code == 200
    assert response.json()["email"] == "original@example.com"
    assert "password_hash" not in response.json()
    assert "mentor_code" not in response.json()


def test_profile_patch_rejects_protected_fields(client):
    http, _, _ = client
    response = http.patch("/api/v1/profile", json={"role": "admin"})
    assert response.status_code == 422


def test_profile_patch_updates_name_and_preserves_email(client):
    http, user, db = client
    response = http.patch("/api/v1/profile", json={"name": " Нова "})
    assert response.status_code == 200
    assert response.json()["name"] == "Нова"
    assert user.email == "original@example.com"
    db.commit.assert_called_once()


def test_preferences_can_turn_email_off_and_change_style(client):
    http, user, db = client
    response = http.patch("/api/v1/profile/preferences", json={
        "email_reminders_enabled": False, "message_style": "zen"
    })
    assert response.status_code == 200
    assert user.message_style == "zen"
    assert user.email_reminders_enabled is False
    db.commit.assert_called_once()


def test_invalid_current_password_does_not_logout(client, monkeypatch):
    http, user, db = client
    monkeypatch.setattr(
        profile_service, "verify_password", lambda password, digest: False
    )
    response = http.put("/api/v1/profile/password", json={
        "current_password": "wrong",
        "new_password": "newpassword123",
    })
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "CURRENT_PASSWORD_INCORRECT"
    assert user.token_version == 0
    db.commit.assert_not_called()


def test_valid_password_change_revokes_old_sessions(client, monkeypatch):
    http, user, db = client
    monkeypatch.setattr(
        profile_service,
        "verify_password",
        lambda password, digest: password == "oldpassword",
    )
    monkeypatch.setattr(
        profile_service, "hash_password", lambda password: "new-digest"
    )
    response = http.put("/api/v1/profile/password", json={
        "current_password": "oldpassword",
        "new_password": "newpassword123",
    })
    assert response.status_code == 204
    assert user.password_hash == "new-digest"
    assert user.token_version == 1
    db.commit.assert_called_once()
