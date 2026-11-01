import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.security import (
    CurrentUser,
    create_access_token,
    get_current_user,
    require_role,
)
from backend.app.db.models.user import User


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET", "security-regression-test-secret-at-least-32-chars"
    )


def credentials(token):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


@pytest.mark.parametrize(
    "role",
    ["user", "mentor", "admin"],
)
def test_valid_tokens(role, registered_users, calendar_db):
    user_id = registered_users[0][0]["user_id"]
    account = calendar_db.get(User, user_id)
    account.role = role
    calendar_db.commit()
    token = create_access_token(user_id, account.token_version)
    user = get_current_user(credentials(token), db=calendar_db)
    assert user == CurrentUser(user_id=user_id, role=role)


def test_zero_subject_is_rejected(calendar_db):
    token = create_access_token(0, 0)
    with pytest.raises(HTTPException) as error:
        get_current_user(credentials(token), db=calendar_db)
    assert error.value.status_code == 401


@pytest.mark.parametrize(
    "token",
    [
        "guest-42",
        "user-",
        "user-abc",
        "-42",
        "user--42",
        "user-42-extra",
    ],
)
def test_invalid_tokens(token, calendar_db):
    with pytest.raises(HTTPException) as error:
        get_current_user(credentials(token), db=calendar_db)
    assert error.value.status_code == 401


def test_missing_credentials():
    with pytest.raises(HTTPException) as error:
        get_current_user(None)
    assert error.value.status_code == 401


@pytest.mark.parametrize("role", ["user", "mentor", "admin"])
def test_allowed_role(role):
    user = CurrentUser(user_id=42, role=role)
    checker = require_role(role)
    assert checker(user) == user


def test_insufficient_role():
    user = CurrentUser(user_id=42, role="user")
    checker = require_role("admin")
    with pytest.raises(HTTPException) as error:
        checker(user)
    assert error.value.status_code == 403
