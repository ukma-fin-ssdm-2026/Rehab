# AI-GENERATED START
"""Адмінські маршрути: ролі, блокування, анонімна діаграма тригерів.

Справжні SQLAlchemy-запити виконуються на in-memory SQLite (лише таблиця
users), без PostgreSQL. Це тестова заміна: PostgreSQL-поведінку перевіряють
тести з conftest Поліни. Записи календаря підміняє list_relapse_entries.
"""

import datetime as dt

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import security
from backend.app.db.base import Base
from backend.app.db.models.user import User
from backend.app.main import http_exception_handler, validation_exception_handler
from backend.app.models import DayStatus, EntryOut, TriggerCategory
from backend.app.routers import admin

SECRET = "admin-test-secret-at-least-32-characters-long"


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[User.__table__])
    with Session(engine, expire_on_commit=False) as db:
        yield db
    engine.dispose()


@pytest.fixture
def client(session):
    app = FastAPI()
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(admin.router, prefix="/api/v1")

    @app.get("/api/v1/probe")
    def probe(user: security.CurrentUser = Depends(security.get_current_user)):
        return {"user_id": user.user_id}

    app.dependency_overrides[security._db_session] = lambda: session
    return TestClient(app)


def make_user(session, role="user", email=None, **extra):
    user = User(
        name=role.title(),
        nickname=role,
        email=email or f"{role}{session.query(User).count()}@example.test",
        password_hash="test-only-hash",
        role=role,
        tracking_start_date=dt.date(2026, 1, 1),
        **extra,
    )
    session.add(user)
    session.commit()
    return user


def auth(user):
    token = security.create_access_token(user.user_id, user.token_version)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(session):
    return make_user(session, "admin")


ROUTES = [
    ("get", "/api/v1/admin/users"),
    ("patch", "/api/v1/admin/users/1/block"),
    ("get", "/api/v1/admin/trigger-distribution"),
]


def call(client, method, url, headers=None):
    kwargs = {"headers": headers or {}}
    if method == "patch":
        kwargs["json"] = {"is_blocked": True}
    return getattr(client, method)(url, **kwargs)


@pytest.mark.parametrize("method,url", ROUTES)
def test_admin_routes_without_token_return_401(client, method, url):
    response = call(client, method, url)

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize("role", ["user", "mentor"])
@pytest.mark.parametrize("method,url", ROUTES)
def test_admin_routes_for_user_and_mentor_return_403(
    client, session, role, method, url
):
    response = call(client, method, url, auth(make_user(session, role)))

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_users_list_is_paginated_and_has_no_secrets(client, session, admin_user):
    for _ in range(3):
        make_user(session, "user")

    response = client.get(
        "/api/v1/admin/users?limit=2&offset=1", headers=auth(admin_user)
    )

    body = response.json()
    assert response.status_code == 200
    assert (body["total"], body["limit"], body["offset"]) == (4, 2, 1)
    assert len(body["items"]) == 2
    for item in body["items"]:
        assert set(item) == {
            "user_id",
            "name",
            "nickname",
            "email",
            "role",
            "is_blocked",
        }
    assert "password" not in response.text
    assert "token" not in response.text


def test_blocking_rejects_old_token_and_unblocking_does_not_restore_it(
    client, session, admin_user
):
    target = make_user(session, "user")
    old = auth(target)
    assert client.get("/api/v1/probe", headers=old).status_code == 200
    url = f"/api/v1/admin/users/{target.user_id}/block"

    blocked = client.patch(url, json={"is_blocked": True}, headers=auth(admin_user))

    assert blocked.status_code == 200
    assert blocked.json()["is_blocked"] is True
    rejected = client.get("/api/v1/probe", headers=old)
    assert rejected.status_code == 403
    assert rejected.json()["code"] == "ACCOUNT_BLOCKED"

    unblocked = client.patch(url, json={"is_blocked": False}, headers=auth(admin_user))

    assert unblocked.json()["is_blocked"] is False
    assert client.get("/api/v1/probe", headers=old).status_code == 401
    session.refresh(target)
    assert client.get("/api/v1/probe", headers=auth(target)).status_code == 200


def test_repeated_block_is_not_an_error_and_keeps_token_version(
    client, session, admin_user
):
    target = make_user(session, "user")
    url = f"/api/v1/admin/users/{target.user_id}/block"

    first = client.patch(url, json={"is_blocked": True}, headers=auth(admin_user))
    version = session.get(User, target.user_id).token_version
    second = client.patch(url, json={"is_blocked": True}, headers=auth(admin_user))

    assert first.status_code == second.status_code == 200
    assert session.get(User, target.user_id).token_version == version


def test_admin_cannot_block_self_or_another_admin(client, session, admin_user):
    other = make_user(session, "admin", email="other-admin@example.test")

    for target in (admin_user, other):
        response = client.patch(
            f"/api/v1/admin/users/{target.user_id}/block",
            json={"is_blocked": True},
            headers=auth(admin_user),
        )

        assert response.status_code == 403
        assert response.json()["code"] == "ADMIN_BLOCK_NOT_ALLOWED"


def test_block_unknown_user_returns_404(client, admin_user):
    response = client.patch(
        "/api/v1/admin/users/9999/block",
        json={"is_blocked": True},
        headers=auth(admin_user),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def _entries(counts, today):
    entries = []
    for category, count in counts.items():
        for index in range(count):
            entries.append(
                EntryOut(
                    record_id=len(entries) + 1,
                    user_id=100 + index,
                    date=today - dt.timedelta(days=1),
                    status=DayStatus.relapse,
                    trigger_category=category,
                    created_at=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
                )
            )
    return entries


def _patch_entries(monkeypatch, entries):
    captured = {}

    def fake(db, date_from, date_to):
        captured["range"] = (date_from, date_to)
        return entries

    monkeypatch.setattr("backend.app.repositories.entries.list_relapse_entries", fake)
    return captured


def test_distribution_is_30_days_with_correct_shares_and_no_personal_data(
    client, admin_user, monkeypatch
):
    from backend.app.core.clock import today_local

    today = min(today_local(), dt.date.today())
    captured = _patch_entries(
        monkeypatch,
        _entries(
            {
                TriggerCategory.stress: 6,
                TriggerCategory.holiday: 3,
                TriggerCategory.social: 1,
            },
            today,
        ),
    )

    response = client.get(
        "/api/v1/admin/trigger-distribution", headers=auth(admin_user)
    )

    body = response.json()
    assert response.status_code == 200
    assert captured["range"] == (today - dt.timedelta(days=29), today)
    assert (body["period_start"], body["period_end"]) == (
        str(today - dt.timedelta(days=29)),
        str(today),
    )
    shares = {c["category"]: c["percentage"] for c in body["categories"]}
    assert body["total"] == 10
    assert shares == {"stress": 60.0, "holiday": 30.0, "social": 10.0, "other": 0.0}
    assert set(body) == {"period_start", "period_end", "total", "categories"}
    assert "user_id" not in response.text and "comment" not in response.text


def test_distribution_with_no_data_has_zero_total_and_zero_percentages(
    client, admin_user, monkeypatch
):
    _patch_entries(monkeypatch, [])

    body = client.get(
        "/api/v1/admin/trigger-distribution", headers=auth(admin_user)
    ).json()

    assert body["total"] == 0
    assert all(c["count"] == 0 and c["percentage"] == 0.0 for c in body["categories"])


# AI-GENERATED END
