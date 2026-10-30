import pytest
from pydantic import ValidationError

from backend.app.schemas.profile import (
    AvatarDataOut,
    AvatarUploadOut,
    ProfileOut,
    ProfilePasswordRequest,
    ProfilePreferencesRequest,
    ProfileUpdateRequest,
)


def test_edit_profile_trims_names_before_length_checks():
    result = ProfileUpdateRequest(name="  " + "а" * 100 + "  ", nickname="  nick ")
    assert result.name == "а" * 100
    assert result.nickname == "nick"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": "  "},
        {"nickname": "\t "},
        {"name": "a" * 101},
        {"nickname": "b" * 51},
        {"name": None},
        {"name": "Test", "email": "other@example.com"},
        {"role": "admin"},
        {"tracking_start_date": "2020-01-01"},
        {"mentor_code": "PRIVATE"},
    ],
)
def test_edit_profile_rejects_empty_invalid_or_protected_fields(payload):
    with pytest.raises(ValidationError):
        ProfileUpdateRequest.model_validate(payload)


def test_edit_profile_allows_single_field():
    assert ProfileUpdateRequest(name=" New ").name == "New"
    assert ProfileUpdateRequest(nickname=" nick ").nickname == "nick"


@pytest.mark.parametrize("raw", ["short", "x" * 129])
def test_new_password_rejects_invalid_length(raw):
    with pytest.raises(ValidationError):
        ProfilePasswordRequest(current_password="old password", new_password=raw)


def test_password_preserves_whitespace_and_boundary_lengths():
    request = ProfilePasswordRequest(
        current_password=" old secret ",
        new_password=" " + "x" * 8,
    )
    assert request.current_password == " old secret "
    assert request.new_password == " " + "x" * 8
    assert len(ProfilePasswordRequest(
        current_password="old", new_password="x" * 128,
    ).new_password) == 128


@pytest.mark.parametrize(
    "payload",
    [
        {"current_password": "password123", "new_password": "password123"},
        {"new_password": "newpassword"},
        {"current_password": "", "new_password": "password123"},
        {
            "current_password": "password123",
            "new_password": "differentpass",
            "user_id": 42,
        },
    ],
)
def test_password_change_requires_current_password_and_safe_fields(payload):
    with pytest.raises(ValidationError):
        ProfilePasswordRequest.model_validate(payload)


@pytest.mark.parametrize("style", ["formal", "humorous", "zen", "strict"])
def test_preferences_accept_all_message_styles(style):
    assert ProfilePreferencesRequest(message_style=style).message_style == style


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message_style": None},
        {"email_reminders_enabled": None},
        {"message_style": "playful"},
        {"email_reminders_enabled": "yes"},
        {"email_reminders_enabled": 1},
        {"message_style": "zen", "user_id": 123},
    ],
)
def test_preferences_reject_unsupported_values(payload):
    with pytest.raises(ValidationError):
        ProfilePreferencesRequest.model_validate(payload)


def test_preferences_allow_disabling_email_without_other_fields():
    data = ProfilePreferencesRequest(email_reminders_enabled=False)
    assert data.email_reminders_enabled is False
    assert data.message_style is None


def test_profile_response_contract_preserves_public_fields():
    data = ProfileOut(
        user_id=1,
        name="Анна",
        nickname="anna",
        email="anna@example.com",
        has_avatar=False,
        avatar_version=None,
        email_reminders_enabled=False,
        message_style="formal",
    )
    assert "password_hash" not in data.model_dump()
    assert data.avatar_version is None
    assert data.message_style == "formal"


def test_avatar_response_version_is_positive():
    assert AvatarUploadOut(has_avatar=True, avatar_version=1).avatar_version == 1
    assert AvatarDataOut(
        data_url="data:image/jpeg;base64,YQ==",
        avatar_version=2,
    ).avatar_version == 2
    with pytest.raises(ValidationError):
        AvatarUploadOut(has_avatar=True, avatar_version=0)
