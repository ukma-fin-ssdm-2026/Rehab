# AI-GENERATED START
"""Адмінські маршрути: ролі та анонімна діаграма тригерів.

SQLAlchemy-запити виконуються на ізольованій PostgreSQL зі спільними
міграціями. Записи календаря для аналітики підміняє list_relapse_entries.
"""

import datetime as dt

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

pytest.importorskip(
    "backend.app.db.base",
    reason="DB-шар (PR Поліни) ще не в цій гілці; тест виконається після його злиття",
)

from backend.app import security  # noqa: E402
from backend.app.db.models.user import User  # noqa: E402
from backend.app.main import (  # noqa: E402
    http_exception_handler,
    validation_exception_handler,
)
from backend.app.models import DayStatus, EntryOut, TriggerCategory  # noqa: E402
from backend.app.routers import admin  # noqa: E402

SECRET = "admin-test-secret-at-least-32-characters-long"


@pytest.fixture
def session(monkeypatch, calendar_db):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    yield calendar_db


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
    ("get", "/api/v1/admin/complaints"),
    ("get", "/api/v1/admin/complaints/1"),
    ("patch", "/api/v1/admin/complaints/1"),
    ("get", "/api/v1/admin/overview"),
    ("get", "/api/v1/admin/trigger-distribution"),
]


def call(client, method, url, headers=None):
    kwargs = {"headers": headers or {}}
    if method == "patch":
        kwargs["json"] = {"decision": "rejected"}
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


@pytest.mark.parametrize(
    "method,url",
    [("get", "/api/v1/admin/users"), ("patch", "/api/v1/admin/users/1/block")],
)
def test_old_account_list_and_block_routes_are_removed(client, admin_user, method, url):
    response = call(client, method, url, auth(admin_user))

    assert response.status_code in (404, 405)


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

    today = today_local()
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
