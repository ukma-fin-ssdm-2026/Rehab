import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.app import security


@pytest.fixture
def protected_client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "local-regression-test-secret-with-32-plus-chars")
    account = SimpleNamespace(user_id=42, role="user", is_blocked=False, token_version=0)
    fake_repository = types.ModuleType("backend.app.repositories.users")
    fake_repository.get_user = lambda db, user_id: account if user_id == 42 else None
    monkeypatch.setitem(sys.modules, "backend.app.repositories.users", fake_repository)

    app = FastAPI()
    app.dependency_overrides[security._db_session] = lambda: object()

    @app.get("/protected")
    def protected(user: security.CurrentUser = Depends(security.get_current_user)):
        return {"user_id": user.user_id, "role": user.role}

    @app.get("/admin")
    def admin(user: security.CurrentUser = Depends(security.require_role("admin"))):
        return {"user_id": user.user_id}

    with TestClient(app) as client:
        yield client


def test_signed_token_works_as_protected_route_dependency(protected_client):
    token = security.create_access_token(42, 0)
    response = protected_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"user_id": 42, "role": "user"}


def test_old_demo_token_is_not_accepted(protected_client):
    response = protected_client.get("/protected", headers={"Authorization": "Bearer user-42"})
    assert response.status_code == 401


def test_missing_token_is_rejected(protected_client):
    response = protected_client.get("/protected")
    assert response.status_code == 401

def test_token_subject_cannot_be_overridden_by_query(protected_client):
    token = security.create_access_token(42, 0)
    response = protected_client.get("/protected?user_id=999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == 42


def test_admin_route_rejects_regular_user(protected_client):
    token = security.create_access_token(42, 0)
    response = protected_client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"
