
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.security import (
    CurrentUser,
    get_current_user,
    require_role,
)


def credentials(token):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


@pytest.mark.parametrize(
    ("token", "user_id", "role"),
    [
        ("user-42", 42, "user"),
        ("mentor-7", 7, "mentor"),
        ("admin-1", 1, "admin"),
        ("user-0", 0, "user"),
    ],
)
def test_valid_tokens(token, user_id, role):
    user = get_current_user(credentials(token))
    assert user == CurrentUser(user_id=user_id, role=role)


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
def test_invalid_tokens(token):
    with pytest.raises(HTTPException) as error:
        get_current_user(credentials(token))
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
