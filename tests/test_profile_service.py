from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from backend.app.schemas.profile import (
    ProfilePasswordRequest,
    ProfilePreferencesRequest,
    ProfileUpdateRequest,
)
from backend.app.services import profile


def make_user():
    return SimpleNamespace(
        user_id=7,
        name="Старе ім'я",
        nickname="old",
        email="original@example.com",
        role="user",
        token_version=2,
        password_hash="hashed-old",
        email_reminders_enabled=False,
        message_style="formal",
    )


def test_profile_edit_only_changes_named_fields(monkeypatch):
    user = make_user()
    db = Mock()
    monkeypatch.setattr(profile, "profile_result", lambda db, account: account)
    updated = profile.change_profile_fields(
        db, user, ProfileUpdateRequest(name=" Нова "),
    )
    assert updated.name == "Нова"
    assert updated.nickname == "old"
    assert updated.email == "original@example.com"
    assert updated.token_version == 2
    db.commit.assert_called_once()


def test_preferences_persist_and_preserve_other_values(monkeypatch):
    user = make_user()
    db = Mock()
    monkeypatch.setattr(profile, "profile_result", lambda db, account: account)
    updated = profile.change_profile_preferences(
        db, user, ProfilePreferencesRequest(message_style="zen"),
    )
    assert updated.message_style == "zen"
    assert updated.email_reminders_enabled is False
    db.commit.assert_called_once()


def test_incorrect_password_preserves_session(monkeypatch):
    user = make_user()
    db = Mock()
    monkeypatch.setattr(profile, "verify_password", lambda password, hash: False)
    with pytest.raises(HTTPException) as error:
        profile.change_profile_password(db, user, "wrong", "new-password123")
    assert error.value.status_code == 400
    assert error.value.detail["code"] == "CURRENT_PASSWORD_INCORRECT"
    assert user.token_version == 2
    assert user.password_hash == "hashed-old"
    db.commit.assert_not_called()


def test_successful_password_change_revokes_existing_tokens(monkeypatch):
    user = make_user()
    db = Mock()
    monkeypatch.setattr(
        profile, "verify_password", lambda password, hash: password == "old-password"
    )
    monkeypatch.setattr(profile, "hash_password", lambda password: f"hashed-{password}")
    profile.change_profile_password(db, user, "old-password", "new-password123")
    assert user.password_hash == "hashed-new-password123"
    assert user.token_version == 3
    db.commit.assert_called_once()


def test_reusing_existing_password_is_rejected_without_revocation(monkeypatch):
    user = make_user()
    db = Mock()
    monkeypatch.setattr(profile, "verify_password", lambda password, hash: True)
    with pytest.raises(HTTPException) as error:
        profile.change_profile_password(db, user, "old-password", "old-password")
    assert error.value.status_code == 422
    assert user.token_version == 2
    db.commit.assert_not_called()


def test_missing_user_does_not_disclose_an_account(monkeypatch):
    monkeypatch.setattr(profile, "get_user", lambda db, user_id: None)
    with pytest.raises(HTTPException) as error:
        profile.require_profile_user(object(), 42)
    assert error.value.status_code == 401
