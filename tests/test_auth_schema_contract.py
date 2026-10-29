"""Контрактні тести Auth перед підключенням PostgreSQL."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.auth import LoginRequest, RegisterRequest


def test_register_normalizes_email_and_names():
    request = RegisterRequest(
        name=" Настя ",
        nickname=" Nastia ",
        email="  NASTIA@Example.COM ",
        password=" pass word ",
    )
    assert request.name == "Настя"
    assert request.nickname == "Nastia"
    assert request.email == "nastia@example.com"
    assert request.password == " pass word "


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", " "),
        ("nickname", "   "),
        ("name", "x" * 101),
        ("nickname", "x" * 51),
        ("email", "bad-email"),
        ("email", "x @example.com"),
        ("email", "a@@example.com"),
        ("password", "short"),
        ("password", "x" * 129),
    ],
)
def test_registration_rejects_invalid_fields(field, value):
    kwargs = {
        "name": "Name",
        "nickname": "Nick",
        "email": "test@example.com",
        "password": "12345678",
    }
    kwargs[field] = value
    with pytest.raises(ValidationError):
        RegisterRequest(**kwargs)


def test_registration_forbids_user_supplied_role():
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="Name",
            nickname="Nick",
            email="test@example.com",
            password="12345678",
            role="admin",
        )


def test_login_normalizes_email_but_not_password():
    result = LoginRequest(email="  USER@EXAMPLE.COM  ", password=" pass word ")
    assert result.email == "user@example.com"
    assert result.password == " pass word "
