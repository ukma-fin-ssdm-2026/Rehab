from sqlalchemy import func, select

from backend.app.db.models.user import User

AUTH = "/api/v1/auth"
PASSWORD = "integration-password-123"


def test_duplicate_email_is_rejected_by_real_database(
    authenticated_calendar, registered_users, calendar_db
):
    account, _ = registered_users[0]
    response = authenticated_calendar.post(
        f"{AUTH}/register",
        json={
            "name": "Second registration",
            "nickname": "second-registration",
            "email": f"  {account['email'].upper()}  ",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_ALREADY_EXISTS"
    assert calendar_db.scalar(select(func.count()).select_from(User)) == 2


def test_registration_cannot_create_admin_by_request(
    authenticated_calendar, calendar_db
):
    response = authenticated_calendar.post(
        f"{AUTH}/register",
        json={
            "name": "Intruder",
            "nickname": "intruder",
            "email": "intruder@example.test",
            "password": PASSWORD,
            "role": "admin",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert calendar_db.scalar(select(func.count()).select_from(User)) == 0


def test_wrong_password_and_unknown_email_do_not_disclose_accounts(
    authenticated_calendar, registered_users
):
    account, _ = registered_users[0]
    wrong_password = authenticated_calendar.post(
        f"{AUTH}/login",
        json={"email": account["email"], "password": "not-the-real-password"},
    )
    unknown_email = authenticated_calendar.post(
        f"{AUTH}/login",
        json={"email": "unknown@example.test", "password": PASSWORD},
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["code"] == "UNAUTHORIZED"


def test_logout_revokes_other_tokens_but_not_other_accounts(
    authenticated_calendar, registered_users
):
    first, first_headers = registered_users[0]
    second, second_headers = registered_users[1]
    another_login = authenticated_calendar.post(
        f"{AUTH}/login",
        json={"email": first["email"], "password": PASSWORD},
    )
    assert another_login.status_code == 200
    another_headers = {
        "Authorization": f"Bearer {another_login.json()['access_token']}"
    }
    assert (
        authenticated_calendar.get(f"{AUTH}/me", headers=another_headers).status_code
        == 200
    )

    assert (
        authenticated_calendar.post(f"{AUTH}/logout", headers=first_headers).status_code
        == 204
    )
    assert (
        authenticated_calendar.get(f"{AUTH}/me", headers=first_headers).status_code
        == 401
    )
    assert (
        authenticated_calendar.get(f"{AUTH}/me", headers=another_headers).status_code
        == 401
    )
    another_account = authenticated_calendar.get(f"{AUTH}/me", headers=second_headers)
    assert another_account.status_code == 200
    assert another_account.json()["user_id"] == second["user_id"]
    assert (
        authenticated_calendar.post(
            f"{AUTH}/login",
            json={"email": first["email"], "password": PASSWORD},
        ).status_code
        == 200
    )


def test_auth_me_rejects_tampered_jwt_and_missing_token(
    authenticated_calendar, registered_users
):
    _, headers = registered_users[0]
    token = headers["Authorization"].removeprefix("Bearer ")
    tampered = f"{token.rsplit('.', 1)[0]}.tampered"
    assert authenticated_calendar.get(f"{AUTH}/me").status_code == 401
    rejected = authenticated_calendar.get(
        f"{AUTH}/me", headers={"Authorization": f"Bearer {tampered}"}
    )
    assert rejected.status_code == 401
    assert rejected.json()["code"] == "UNAUTHORIZED"
