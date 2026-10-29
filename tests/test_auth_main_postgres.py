import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.security import _db_session
from backend.app.services.auth import hash_password

API = "/api/v1"
PASSWORD = "integration-password-123"


@pytest.fixture
def main_api(calendar_db, postgres_schema, monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET", "main-app-integration-test-secret-at-least-32-characters"
    )

    def test_database():
        with Session(postgres_schema, expire_on_commit=False) as db:
            try:
                yield db
            except BaseException:
                db.rollback()
                raise

    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = test_database
    app.dependency_overrides[_db_session] = test_database
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def register(client, email):
    response = client.post(
        f"{API}/auth/register",
        json={
            "name": "Integration",
            "nickname": "integration",
            "email": email,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client, email, password=PASSWORD):
    response = client.post(
        f"{API}/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_main_app_register_calendar_goal_stats_and_logout(main_api):
    assert main_api.get("/health").status_code == 200
    assert main_api.get("/ready").status_code == 200

    account = register(main_api, "first@main-integration.test")
    headers = login(main_api, account["email"])
    profile = main_api.get(f"{API}/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["user_id"] == account["user_id"]
    assert "password_hash" not in profile.json()

    entry = main_api.post(
        f"{API}/calendar/entries",
        headers=headers,
        json={"date": today_local().isoformat(), "status": "sober"},
    )
    assert entry.status_code == 201, entry.text
    entries = main_api.get(f"{API}/calendar/entries", headers=headers)
    assert entries.status_code == 200
    assert entries.json()["total"] == 1
    assert entries.json()["items"][0]["user_id"] == account["user_id"]

    goals = main_api.get(f"{API}/goals", headers=headers)
    assert goals.status_code == 200, goals.text
    assert [item["target_days"] for item in goals.json()["items"]] == [7, 30]
    assert goals.json()["items"][0]["is_achieved"] is False
    stats = main_api.get(f"{API}/statistics", headers=headers)
    assert stats.status_code == 200, stats.text

    assert main_api.post(f"{API}/auth/logout", headers=headers).status_code == 204
    assert main_api.get(f"{API}/auth/me", headers=headers).status_code == 401
    assert main_api.get(f"{API}/calendar/entries", headers=headers).status_code == 401


def test_main_app_isolates_accounts_and_admin_revokes_session(
    main_api, postgres_schema
):
    first = register(main_api, "first@main-integration.test")
    second = register(main_api, "second@main-integration.test")
    first_headers = login(main_api, first["email"])
    second_headers = login(main_api, second["email"])

    entry = main_api.post(
        f"{API}/calendar/entries",
        headers=first_headers,
        json={"date": today_local().isoformat(), "status": "sober"},
    )
    assert entry.status_code == 201, entry.text
    other_entries = main_api.get(f"{API}/calendar/entries", headers=second_headers)
    assert other_entries.status_code == 200
    assert other_entries.json()["total"] == 0
    assert (
        main_api.get(
            f"{API}/calendar/entries/{entry.json()['record_id']}",
            headers=second_headers,
        ).status_code
        == 404
    )
    assert main_api.get(f"{API}/admin/users", headers=first_headers).status_code == 403

    with Session(postgres_schema) as db:
        db.add(
            User(
                name="Test admin",
                nickname="test-admin",
                email="admin@main-integration.test",
                password_hash=hash_password(PASSWORD),
                role="admin",
                tracking_start_date=today_local(),
            )
        )
        db.commit()

    admin_headers = login(main_api, "admin@main-integration.test")
    response = main_api.patch(
        f"{API}/admin/users/{second['user_id']}/block",
        headers=admin_headers,
        json={"is_blocked": True},
    )
    assert response.status_code == 200, response.text
    assert main_api.get(f"{API}/auth/me", headers=second_headers).status_code == 403
    blocked_login = main_api.post(
        f"{API}/auth/login",
        json={"email": second["email"], "password": PASSWORD},
    )
    assert blocked_login.status_code == 403

    unblock = main_api.patch(
        f"{API}/admin/users/{second['user_id']}/block",
        headers=admin_headers,
        json={"is_blocked": False},
    )
    assert unblock.status_code == 200, unblock.text
    assert main_api.get(f"{API}/auth/me", headers=second_headers).status_code == 401
    assert main_api.get(f"{API}/auth/me", headers=first_headers).status_code == 200
    fresh_headers = login(main_api, second["email"])
    assert main_api.get(f"{API}/auth/me", headers=fresh_headers).status_code == 200
