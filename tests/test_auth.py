"""Tests independent of PostgreSQL; DB integration follows Polina's foundation."""
import datetime as dt
import os

import jwt
import pytest
from fastapi import HTTPException

from backend.app.security import create_access_token, decode_access_token
from backend.app.schemas.auth import RegisterRequest


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "secure-unit-test-secret-longer-than-32-characters")


def test_signed_token_round_trip():
    token = create_access_token(42, 2)
    assert decode_access_token(token) == (42, 2)


def test_legacy_demo_token_is_rejected():
    with pytest.raises(HTTPException) as error:
        decode_access_token("user-42")
    assert error.value.status_code == 401


def test_wrong_signature_is_rejected(monkeypatch):
    token = create_access_token(42, 0)
    monkeypatch.setenv("JWT_SECRET", "another-unit-test-secret-longer-than-32-chars")
    with pytest.raises(HTTPException) as error:
        decode_access_token(token)
    assert error.value.status_code == 401


def test_expired_token_is_rejected():
    old = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)
    token = jwt.encode(
        {"sub": "42", "iat": old, "exp": old + dt.timedelta(minutes=10), "token_version": 0},
        os.environ["JWT_SECRET"], algorithm="HS256",
    )
    with pytest.raises(HTTPException) as error:
        decode_access_token(token)
    assert error.value.status_code == 401


def test_role_cannot_be_set_during_registration():
    with pytest.raises(Exception):
        RegisterRequest(
            name="Name", nickname="Nick", email="a@example.com",
            password="12345678", role="admin",
        )


def test_secret_is_required(monkeypatch):
    monkeypatch.delenv("JWT_SECRET")
    with pytest.raises(RuntimeError):
        create_access_token(42, 0)


def test_argon2_password_hash():
    pytest.importorskip("pwdlib")
    from backend.app.services.auth import hash_password, verify_password
    digest = hash_password(" strong pass ")
    assert digest != " strong pass "
    assert digest.startswith("$argon2")
    assert verify_password(" strong pass ", digest)
    assert not verify_password("wrong", digest)
