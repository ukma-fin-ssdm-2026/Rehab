"""KT-1 integration: real auth, Argon2, JWT and migrated PostgreSQL.

AI-GENERATED START: prepared with ChatGPT against the team spec, sections 7/11.
No authentication or progress implementation is replaced in these tests.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local
from backend.app.db.models.user import User
from backend.app.models import EntryCreate
from backend.app.repositories import entries, users
from backend.app.services.auth import verify_password

URL = "/api/v1/calendar/entries"
PASSWORD = "integration-password-123"


@pytest.fixture
def stored_entry(calendar_db, registered_users):
    account, _ = registered_users[0]
    result = entries.create_entry(
        calendar_db, account["user_id"], EntryCreate(date=today_local(), status="sober")
    )
    calendar_db.commit()
    return result


def test_registration_matches_migrated_user_schema(
    authenticated_calendar, registered_users, postgres_schema
):
    account, headers = registered_users[0]
    with Session(postgres_schema) as session:
        stored = session.get(User, account["user_id"])
        assert stored.email == account["email"]
        assert stored.password_hash.startswith("$argon2")
        assert verify_password(PASSWORD, stored.password_hash)
        assert stored.tracking_start_date == today_local()
    response = authenticated_calendar.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["user_id"] == account["user_id"]
    assert "password_hash" not in response.json()


def test_signed_user_reads_persisted_calendar(
    authenticated_calendar, registered_users, stored_entry
):
    _, headers = registered_users[0]
    response = authenticated_calendar.get(URL, headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["record_id"] == stored_entry.record_id
    assert (
        authenticated_calendar.get(
            f"{URL}/{stored_entry.record_id}", headers=headers
        ).json()["status"]
        == "sober"
    )


def test_other_account_cannot_read_or_claim_entry(
    authenticated_calendar, registered_users, stored_entry
):
    owner, _ = registered_users[0]
    _, headers = registered_users[1]
    response = authenticated_calendar.get(
        URL, params={"user_id": owner["user_id"]}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert (
        authenticated_calendar.get(
            f"{URL}/{stored_entry.record_id}", headers=headers
        ).status_code
        == 404
    )


@pytest.mark.parametrize("token", [None, "user-42", "not-a-jwt"])
def test_calendar_rejects_missing_and_demo_sessions(authenticated_calendar, token):
    headers = {} if token is None else {"Authorization": f"Bearer {token}"}
    assert authenticated_calendar.get(URL, headers=headers).status_code == 401


def test_logout_revokes_calendar_access(
    authenticated_calendar, registered_users, stored_entry
):
    _, headers = registered_users[0]
    assert (
        authenticated_calendar.post("/api/v1/auth/logout", headers=headers).status_code
        == 204
    )
    assert authenticated_calendar.get(URL, headers=headers).status_code == 401
    assert (
        authenticated_calendar.patch(
            f"{URL}/{stored_entry.record_id}",
            headers=headers,
            json={"status": "relapse"},
        ).status_code
        == 401
    )


def test_block_and_unblock_do_not_revive_old_session(
    authenticated_calendar, registered_users, calendar_db
):
    account, headers = registered_users[0]
    users.set_blocked(calendar_db, account["user_id"], True)
    calendar_db.commit()
    assert authenticated_calendar.get(URL, headers=headers).status_code == 403
    assert (
        authenticated_calendar.post(
            "/api/v1/auth/login", json={"email": account["email"], "password": PASSWORD}
        ).status_code
        == 403
    )
    users.set_blocked(calendar_db, account["user_id"], False)
    calendar_db.commit()
    assert authenticated_calendar.get(URL, headers=headers).status_code == 401
    login = authenticated_calendar.post(
        "/api/v1/auth/login", json={"email": account["email"], "password": PASSWORD}
    )
    assert login.status_code == 200
    assert (
        authenticated_calendar.get(
            URL, headers={"Authorization": f"Bearer {login.json()['access_token']}"}
        ).status_code
        == 200
    )


def test_authenticated_calendar_write_runs_real_progress(
    authenticated_calendar, registered_users, postgres_schema
):
    _, headers = registered_users[0]
    response = authenticated_calendar.post(
        URL, headers=headers, json={"date": str(today_local()), "status": "sober"}
    )
    assert response.status_code == 201
    with Session(postgres_schema) as session:
        assert (
            entries.count_user_entries(session, registered_users[0][0]["user_id"]) == 1
        )


def test_database_fixtures_register_real_user_model(calendar_db):
    from backend.app.db.base import Base

    assert Base.metadata.tables["users"] is User.__table__
    assert calendar_db.scalar(select(User)) is None


# AI-GENERATED END
