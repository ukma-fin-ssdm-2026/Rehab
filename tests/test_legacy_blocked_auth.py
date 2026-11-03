"""Regression for the removed global account-block policy."""

from sqlalchemy.orm import Session

from backend.app.db.models.user import User


API = "/api/v1"


def test_old_blocked_flag_does_not_reject_existing_or_new_session(
    authenticated_calendar, registered_users, postgres_schema
):
    account, headers = registered_users[0]
    with Session(postgres_schema) as db:
        saved = db.get(User, account["user_id"])
        saved.is_blocked = True
        db.commit()

    assert authenticated_calendar.get(
        f"{API}/auth/me", headers=headers
    ).status_code == 200
    new_login = authenticated_calendar.post(
        f"{API}/auth/login",
        json={
            "email": account["email"],
            "password": "integration-password-123",
        },
    )
    assert new_login.status_code == 200, new_login.text

    with Session(postgres_schema) as db:
        saved = db.get(User, account["user_id"])
        saved.token_version += 1
        db.commit()
    assert authenticated_calendar.get(
        f"{API}/auth/me", headers=headers
    ).status_code == 401
