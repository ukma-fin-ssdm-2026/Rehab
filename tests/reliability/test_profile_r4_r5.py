"""Reliability checks for the Lab 09 database and avatar fixes (R4/R5)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import get_database_url
from backend.app.db import session as sessions
from backend.app.db.models.avatar import UserAvatar
from backend.app.routers import profile
from backend.app.security import CurrentUser
from backend.app.services.avatar import MAX_UPLOAD_BYTES


def profile_client(user_id):
    app = FastAPI()
    app.include_router(profile.router)
    app.dependency_overrides[profile.get_current_user] = lambda: CurrentUser(
        user_id=user_id, role="user"
    )

    app.dependency_overrides[profile._db_session] = sessions.get_db
    return TestClient(app)


@pytest.fixture
def application_test_engine(postgres_schema, monkeypatch):
    engine = sessions._engine_for_url(get_database_url(test=True))
    monkeypatch.setattr(sessions, "get_engine", lambda: engine)
    return engine


def test_avatar_missing_owner_returns_clear_authorization_error(
    application_test_engine, db_users, monkeypatch
):
    user_id = db_users[0]
    monkeypatch.setattr(profile, "normalize_avatar", lambda raw: b"normalized")
    monkeypatch.setattr(profile, "lock_user_for_update", lambda db, uid: None)

    with profile_client(user_id) as client:
        response = client.put(
            "/profile/avatar", content=b"image", headers={"content-type": "image/png"}
        )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHORIZED"
    assert response.json()["detail"]["message"] == "Недійсна сесія"


def test_avatar_database_lock_failure_returns_safe_error_and_keeps_old_image(
    application_test_engine, calendar_db, db_users, monkeypatch
):
    user_id = db_users[0]
    calendar_db.add(UserAvatar(user_id=user_id, image_data=b"old", version=2))
    calendar_db.commit()
    monkeypatch.setattr(profile, "normalize_avatar", lambda raw: b"replacement")

    with Session(application_test_engine) as blocker:
        blocker.execute(
            text("SELECT user_id FROM users WHERE user_id=:id FOR UPDATE"),
            {"id": user_id},
        )
        with profile_client(user_id) as client:
            response = client.put(
                "/profile/avatar",
                content=b"image",
                headers={"content-type": "image/png"},
            )
        assert blocker.in_transaction()
        blocker.rollback()

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "DATABASE_TIMEOUT"
    with Session(application_test_engine) as check:
        avatar = check.get(UserAvatar, user_id)
        assert (avatar.image_data, avatar.version) == (b"old", 2)


def test_avatar_upload_rejects_first_byte_over_size_limit_before_processing(
    application_test_engine, db_users, monkeypatch
):
    user_id = db_users[0]
    normalize_called = False

    def normalize(raw):
        nonlocal normalize_called
        normalize_called = True
        return raw

    monkeypatch.setattr(profile, "normalize_avatar", normalize)
    with profile_client(user_id) as client:
        response = client.put(
            "/profile/avatar",
            content=b"x" * (MAX_UPLOAD_BYTES + 1),
            headers={"content-type": "image/png"},
        )

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "AVATAR_TOO_LARGE"
    assert normalize_called is False
