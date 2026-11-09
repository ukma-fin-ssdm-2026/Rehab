"""R4: exercise application connection limits against guarded test PostgreSQL."""

from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import get_database_url
from backend.app.db import session as sessions
from backend.app.db.models.avatar import UserAvatar
from backend.app.routers import profile
from backend.app.security import CurrentUser


@pytest.fixture
def application_engine(postgres_schema, monkeypatch):
    engine = sessions._engine_for_url(get_database_url(test=True))
    monkeypatch.setattr(sessions, "get_engine", lambda: engine)
    yield engine
    engine.dispose()
    sessions._engine_for_url.cache_clear()


def test_sql_limits_survive_pool_reuse_and_reconnect(application_engine):
    for reconnect in (False, False, True):
        if reconnect:
            application_engine.dispose()
        with application_engine.connect() as conn:
            assert conn.scalar(text("SHOW statement_timeout")) == "10s"
            assert conn.scalar(text("SHOW lock_timeout")) == "2s"


@pytest.mark.parametrize("failure", ["statement", "lock"])
def test_sql_timeout_rolls_back_and_allows_next_request(
    application_engine, calendar_db, db_users, postgres_schema, failure
):
    original = calendar_db.scalar(
        text("SELECT nickname FROM users WHERE user_id=:id"), {"id": db_users[1]}
    )
    with Session(postgres_schema) as blocker:
        blocker.execute(
            text("SELECT user_id FROM users WHERE user_id=:id FOR UPDATE"),
            {"id": db_users[0]},
        )
        with pytest.raises(HTTPException) as caught:
            with contextmanager(sessions.get_db)() as db:
                db.execute(
                    text("UPDATE users SET nickname='not-committed' WHERE user_id=:id"),
                    {"id": db_users[1]},
                )
                if failure == "statement":
                    db.execute(text("SELECT pg_sleep(15)"))
                else:
                    db.execute(
                        text("SELECT user_id FROM users WHERE user_id=:id FOR UPDATE"),
                        {"id": db_users[0]},
                    )
        assert caught.value.status_code == 503
        assert caught.value.detail["code"] == "DATABASE_TIMEOUT"
        assert caught.value.__cause__.orig.sqlstate == (
            "57014" if failure == "statement" else "55P03"
        )
        blocker.rollback()

    with contextmanager(sessions.get_db)() as db:
        assert db.scalar(text("SELECT 1")) == 1
        assert db.scalar(
            text("SELECT nickname FROM users WHERE user_id=:id"), {"id": db_users[1]}
        ) == original
        db.execute(
            text("UPDATE users SET nickname='recovered' WHERE user_id=:id"),
            {"id": db_users[1]},
        )
        db.commit()
    with Session(application_engine) as check:
        assert check.scalar(
            text("SELECT nickname FROM users WHERE user_id=:id"), {"id": db_users[1]}
        ) == "recovered"


def test_avatar_lock_timeout_returns_safe_http_error_and_preserves_avatar(
    application_engine, calendar_db, db_users, postgres_schema, monkeypatch
):
    user_id = db_users[0]
    calendar_db.add(UserAvatar(user_id=user_id, image_data=b"original", version=3))
    calendar_db.commit()
    monkeypatch.setattr(profile, "normalize_avatar", lambda raw: b"replacement")
    app = FastAPI()
    app.include_router(profile.router)
    app.dependency_overrides[profile.get_current_user] = lambda: CurrentUser(
        user_id=user_id, role="user"
    )
    app.dependency_overrides[profile._db_session] = sessions.get_db
    with Session(postgres_schema) as blocker:
        blocker.execute(
            text("SELECT user_id FROM users WHERE user_id=:id FOR UPDATE"),
            {"id": user_id},
        )
        with TestClient(app) as client:
            result = client.put(
                "/profile/avatar", content=b"image", headers={"content-type": "image/png"}
            )
        assert result.status_code == 503
        assert result.json() == {"detail": {
            "code": "DATABASE_TIMEOUT",
            "message": "База даних не відповіла вчасно. Перевірте стан операції перед повтором.",
            "details": None,
        }}
        blocker.rollback()
    with Session(application_engine) as check:
        avatar = check.get(UserAvatar, user_id)
        assert (avatar.version, avatar.image_data) == (3, b"original")
