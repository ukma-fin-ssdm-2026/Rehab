import datetime as dt
import importlib
import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app import security


@pytest.fixture
def app_client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "http-test-secret-string-longer-than-32-characters")
    users = {}
    next_id = [1]
    fake_db = SimpleNamespace(commit=lambda: None, refresh=lambda account: None, flush=lambda: None)

    def get_user(db, uid):
        return users.get(uid)

    def get_user_by_email(db, email):
        return next((u for u in users.values() if u.email == email), None)

    def create_user(db, **kwargs):
        uid = next_id[0]
        next_id[0] += 1
        account = SimpleNamespace(
            user_id=uid, name=kwargs["name"], nickname=kwargs["nickname"],
            email=kwargs["email"], password_hash=kwargs["password_hash"],
            tracking_start_date=kwargs["tracking_start_date"],
            token_version=0, role="user", is_blocked=False,
        )
        users[uid] = account
        return account

    def revoke_sessions(db, account):
        account.token_version += 1

    fake_repo = types.ModuleType("backend.app.repositories.users")
    fake_repo.get_user = get_user
    fake_repo.get_user_by_email = get_user_by_email
    fake_repo.create_user = create_user
    fake_repo.revoke_sessions = revoke_sessions
    monkeypatch.setitem(sys.modules, "backend.app.repositories.users", fake_repo)
    fake_clock = types.ModuleType("backend.app.core.clock")
    fake_clock.today_local = lambda: dt.date(2026, 10, 29)
    monkeypatch.setitem(sys.modules, "backend.app.core.clock", fake_clock)

    router_module = importlib.import_module("backend.app.routers.auth")
    monkeypatch.setattr(router_module, "get_user_by_email", get_user_by_email)
    monkeypatch.setattr(router_module, "create_user", create_user)
    monkeypatch.setattr(router_module, "get_user", get_user)
    monkeypatch.setattr(router_module, "revoke_sessions", revoke_sessions)
    monkeypatch.setattr(router_module, "hash_password", lambda password: "unit_hash_" + password)

    def authenticate(db, email, password):
        account = get_user_by_email(db, email)
        if account is None or account.password_hash != "unit_hash_" + password:
            raise security._unauthorized("Неправильна електронна адреса або пароль")
        return account

    monkeypatch.setattr(router_module, "authenticate", authenticate)
    app = FastAPI()
    app.include_router(router_module.router, prefix="/api/v1")
    app.dependency_overrides[security._db_session] = lambda: fake_db
    with TestClient(app) as client:
        yield client, users


def register(client, email=" PERSON@Example.com "):
    return client.post("/api/v1/auth/register", json={
        "name": "Person", "nickname": "person", "email": email,
        "password": "test-password-123",
    })


def login(client, email="person@example.com", password="test-password-123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_register_normalizes_email_and_never_returns_hash(app_client):
    client, users = app_client
    r = register(client)
    assert r.status_code == 201
    assert r.json()["email"] == "person@example.com"
    assert r.json()["role"] == "user"
    assert "password" not in r.json()
    assert "password_hash" not in r.json()
    assert users[1].password_hash != "test-password-123"


def test_duplicate_email_returns_409(app_client):
    client, _ = app_client
    assert register(client).status_code == 201
    r = register(client, "person@example.com")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_login_me_logout_revokes_token(app_client):
    client, _ = app_client
    assert register(client).status_code == 201
    signed_in = login(client)
    assert signed_in.status_code == 200
    token = signed_in.json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "person@example.com"
    assert me.json()["current_date"] == "2026-10-29"
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_wrong_password_and_missing_token(app_client):
    client, _ = app_client
    register(client)
    assert login(client, password="wrong").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


def test_legacy_block_flag_no_longer_prevents_authentication(app_client):
    client, users = app_client
    register(client)
    token = login(client).json()["access_token"]
    users[1].is_blocked = True
    assert client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer " + token,
    }).status_code == 200
    assert login(client).status_code == 200


def test_register_rejects_admin_role_and_invalid_fields(app_client):
    client, _ = app_client
    payload = {
        "name": "N", "nickname": "NN", "email": "n@example.com",
        "password": "12345678", "role": "admin",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 422
    payload.pop("role")
    payload["password"] = "short"
    assert client.post("/api/v1/auth/register", json=payload).status_code == 422
