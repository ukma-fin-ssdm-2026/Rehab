"""Unit tests for session revocation/blocking with a fake repository, no DB writes."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app import security


@pytest.fixture(autouse=True)
def secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "another-unit-test-secret-with-adequate-length")


def check_token(monkeypatch, account, token):
    from types import ModuleType
    import sys
    repo = ModuleType("backend.app.repositories.users")
    repo.get_user = lambda db, uid: account if uid == account.user_id else None
    monkeypatch.setitem(sys.modules, "backend.app.repositories.users", repo)
    return security.get_current_user(
        credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        db=object(),
    )


def test_valid_session(monkeypatch):
    user = SimpleNamespace(user_id=7, role="user", is_blocked=False, token_version=0)
    value = check_token(monkeypatch, user, security.create_access_token(7, 0))
    assert (value.user_id, value.role) == (7, "user")


def test_revoked_token(monkeypatch):
    user = SimpleNamespace(user_id=7, role="user", is_blocked=False, token_version=1)
    with pytest.raises(HTTPException) as error:
        check_token(monkeypatch, user, security.create_access_token(7, 0))
    assert error.value.status_code == 401


def test_blocked_user(monkeypatch):
    user = SimpleNamespace(user_id=7, role="user", is_blocked=True, token_version=0)
    with pytest.raises(HTTPException) as error:
        check_token(monkeypatch, user, security.create_access_token(7, 0))
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "ACCOUNT_BLOCKED"


def test_role_comes_from_database(monkeypatch):
    user = SimpleNamespace(user_id=7, role="admin", is_blocked=False, token_version=0)
    current = check_token(monkeypatch, user, security.create_access_token(7, 0))
    assert current.role == "admin"


def test_unknown_account(monkeypatch):
    user = SimpleNamespace(user_id=7, role="user", is_blocked=False, token_version=0)
    with pytest.raises(HTTPException) as error:
        check_token(monkeypatch, user, security.create_access_token(8, 0))
    assert error.value.status_code == 401

def test_blocking_takes_precedence_over_revocation(monkeypatch):
    """A blocked account must return 403 even after token_version is raised."""
    user = SimpleNamespace(user_id=7, role="user", is_blocked=True, token_version=1)
    with pytest.raises(HTTPException) as error:
        check_token(monkeypatch, user, security.create_access_token(7, 0))
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "ACCOUNT_BLOCKED"
