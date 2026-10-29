import pytest
from pydantic import ValidationError

from backend.app.schemas.auth import RegisterRequest

BASE = {
    "name": "N",
    "nickname": "Nick",
    "email": "user@example.com",
    "password": "password123",
}


@pytest.mark.parametrize(
    "field, raw, normalized",
    [
        ("name", "  " + "a" * 100 + "  ", "a" * 100),
        ("nickname", "  " + "a" * 50 + " ", "a" * 50),
        ("email", "  USER@EXAMPLE.COM  ", "user@example.com"),
    ],
)
def test_trim_before_length_validation(field, raw, normalized):
    account = RegisterRequest(**{**BASE, field: raw})
    assert getattr(account, field) == normalized


@pytest.mark.parametrize(
    "field, raw",
    [
        ("name", " " + "a" * 101 + " "),
        ("nickname", " " + "b" * 51 + " "),
        ("email", " " + "a" * 245 + "@example.com" + " "),
    ],
)
def test_overlong_after_trim_rejected(field, raw):
    with pytest.raises(ValidationError):
        RegisterRequest(**{**BASE, field: raw})


def test_password_preserves_spaces():
    account = RegisterRequest(**{**BASE, "password": " password123 "})
    assert account.password == " password123 "


def test_role_prohibited():
    with pytest.raises(ValidationError):
        RegisterRequest(**{**BASE, "role": "admin"})
