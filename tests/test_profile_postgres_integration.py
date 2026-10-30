"""Profile smoke against real migrated PostgreSQL and signed JWTs.

Uses the existing guarded TEST_DATABASE_URL fixture; never contacts the
production database or sends email. The app is assembled without modifying
Sofiia's shared backend/app/main.py until the agreed integration checkpoint.
"""

import base64
from io import BytesIO

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from backend.app.db.models.avatar import UserAvatar
from backend.app.db.models.user import User
from backend.app.routers import profile as profile_router

API = "/api/v1"
OLD_PASSWORD = "integration-password-123"
NEW_PASSWORD = "updated-integration-password-456"


@pytest.fixture
def profile_api(authenticated_calendar):
    """Auth is genuine: only attach the pending profile router to the test app."""
    authenticated_calendar.app.include_router(
        profile_router.router, prefix=API
    )
    return authenticated_calendar


def image_bytes(color, fmt="PNG"):
    out = BytesIO()
    Image.new("RGB", (960, 720), color=color).save(out, format=fmt)
    return out.getvalue()


def upload(client, headers, image, content_type="image/png"):
    return client.put(
        f"{API}/profile/avatar",
        headers={**headers, "Content-Type": content_type},
        content=image,
    )


def test_profile_authenticated_isolation_and_persisted_edit(
    profile_api, registered_users, postgres_schema
):
    first, first_headers = registered_users[0]
    second, second_headers = registered_users[1]

    assert profile_api.get(f"{API}/profile").status_code == 401
    before = profile_api.get(f"{API}/profile", headers=first_headers)
    assert before.status_code == 200, before.text
    assert before.json()["user_id"] == first["user_id"]
    assert before.json()["email"] == first["email"]
    assert before.json()["has_avatar"] is False
    assert before.json()["avatar_version"] is None
    assert before.json()["email_reminders_enabled"] is False
    assert before.json()["message_style"] == "formal"
    assert "password_hash" not in before.json()
    assert "mentor_code" not in before.json()

    for forbidden in (
        {"email": "stolen@example.test"},
        {"role": "admin"},
        {"user_id": second["user_id"]},
        {"mentor_code": "AAAAAAAAAAAA"},
    ):
        rejected = profile_api.patch(
            f"{API}/profile", headers=first_headers, json=forbidden
        )
        assert rejected.status_code == 422, rejected.text

    edited = profile_api.patch(
        f"{API}/profile",
        headers=first_headers,
        json={"name": "  Нове ім'я  ", "nickname": "  updated  "},
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["name"] == "Нове ім'я"
    assert edited.json()["nickname"] == "updated"
    assert edited.json()["email"] == first["email"]

    other = profile_api.get(f"{API}/profile", headers=second_headers)
    assert other.status_code == 200
    assert other.json()["user_id"] == second["user_id"]
    assert other.json()["name"] == second["name"]

    with Session(postgres_schema) as db:
        stored = db.get(User, first["user_id"])
        assert stored.name == "Нове ім'я"
        assert stored.nickname == "updated"
        assert stored.email == first["email"]
        assert stored.role == "user"

    # A different HTTP request/SQL session sees the changes.
    reloaded = profile_api.get(f"{API}/profile", headers=first_headers)
    assert reloaded.json()["nickname"] == "updated"


def test_preferences_are_private_and_survive_new_session(
    profile_api, registered_users, postgres_schema
):
    first, first_headers = registered_users[0]
    _, second_headers = registered_users[1]

    for invalid in ({"message_style": "unknown"}, {"email_reminders_enabled": "true"},
                    {"message_style": None}, {}):
        rejected = profile_api.patch(
            f"{API}/profile/preferences", headers=first_headers, json=invalid
        )
        assert rejected.status_code == 422

    changed = profile_api.patch(
        f"{API}/profile/preferences", headers=first_headers,
        json={"email_reminders_enabled": True, "message_style": "zen"},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["email_reminders_enabled"] is True
    assert changed.json()["message_style"] == "zen"
    assert profile_api.get(
        f"{API}/profile", headers=second_headers
    ).json()["message_style"] == "formal"

    with Session(postgres_schema) as db:
        account = db.get(User, first["user_id"])
        assert account.email_reminders_enabled is True
        assert account.message_style == "zen"

    off = profile_api.patch(
        f"{API}/profile/preferences", headers=first_headers,
        json={"email_reminders_enabled": False},
    )
    assert off.status_code == 200
    assert off.json()["email_reminders_enabled"] is False
    assert off.json()["message_style"] == "zen"


def test_password_error_preserves_session_success_revokes_prior_jwts(
    profile_api, registered_users, postgres_schema
):
    first, old_headers = registered_users[0]
    _, other_headers = registered_users[1]
    old_token = old_headers["Authorization"]

    wrong = profile_api.put(
        f"{API}/profile/password", headers=old_headers,
        json={
            "current_password": "not-the-old-password",
            "new_password": NEW_PASSWORD,
        },
    )
    assert wrong.status_code == 400, wrong.text
    assert wrong.json()["detail"]["code"] == "CURRENT_PASSWORD_INCORRECT"
    assert profile_api.get(f"{API}/auth/me", headers=old_headers).status_code == 200

    # A separate simultaneous login simulates an older second device.
    second_login = profile_api.post(
        f"{API}/auth/login", json={"email": first["email"], "password": OLD_PASSWORD}
    )
    assert second_login.status_code == 200, second_login.text
    second_device_headers = {
        "Authorization": "Bearer " + second_login.json()["access_token"]
    }

    changed = profile_api.put(
        f"{API}/profile/password", headers=old_headers,
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert changed.status_code == 204, changed.text

    for headers in (old_headers, second_device_headers):
        assert profile_api.get(f"{API}/auth/me", headers=headers).status_code == 401
        assert profile_api.get(f"{API}/profile", headers=headers).status_code == 401
    assert profile_api.get(f"{API}/auth/me", headers=other_headers).status_code == 200

    old_login = profile_api.post(
        f"{API}/auth/login", json={"email": first["email"], "password": OLD_PASSWORD}
    )
    assert old_login.status_code == 401
    new_login = profile_api.post(
        f"{API}/auth/login", json={"email": first["email"], "password": NEW_PASSWORD}
    )
    assert new_login.status_code == 200, new_login.text
    fresh = {"Authorization": "Bearer " + new_login.json()["access_token"]}
    assert fresh["Authorization"] != old_token
    assert profile_api.get(f"{API}/profile", headers=fresh).status_code == 200

    with Session(postgres_schema) as db:
        stored = db.get(User, first["user_id"])
        assert stored.token_version == 1
        assert stored.password_hash != OLD_PASSWORD


def test_avatar_private_replace_failed_upload_and_persistence(
    profile_api, registered_users, postgres_schema
):
    first, headers = registered_users[0]
    _, other_headers = registered_users[1]
    assert profile_api.get(f"{API}/profile/avatar", headers=headers).status_code == 404
    assert profile_api.get(f"{API}/profile/avatar").status_code == 401

    first_upload = upload(profile_api, headers, image_bytes("#008800"))
    assert first_upload.status_code == 200, first_upload.text
    assert first_upload.json() == {"has_avatar": True, "avatar_version": 1}
    assert first_upload.headers["cache-control"] == "no-store"
    avatar = profile_api.get(f"{API}/profile/avatar", headers=headers)
    assert avatar.status_code == 200, avatar.text
    assert avatar.headers["cache-control"] == "no-store"
    assert avatar.json()["avatar_version"] == 1
    data_url = avatar.json()["data_url"]
    assert data_url.startswith("data:image/jpeg;base64,")
    decoded = base64.b64decode(data_url.split(",", 1)[1], validate=True)
    with Image.open(BytesIO(decoded)) as saved:
        assert saved.format == "JPEG"
        assert max(saved.size) <= 512
        assert saved.info.get("exif") is None
    assert len(decoded) <= 256 * 1024

    # No other JWT can read the first user's avatar.
    assert profile_api.get(
        f"{API}/profile/avatar", headers=other_headers
    ).status_code == 404
    assert profile_api.get(
        f"{API}/profile", headers=other_headers
    ).json()["has_avatar"] is False

    for invalid, content_type, code in (
        (b"not an image", "image/png", 422),
        (b"GIF89a", "image/gif", 422),
        (b"x" * (5 * 1024 * 1024 + 1), "image/jpeg", 413),
    ):
        refused = upload(profile_api, headers, invalid, content_type)
        assert refused.status_code == code
        assert profile_api.get(
            f"{API}/profile/avatar", headers=headers
        ).json()["avatar_version"] == 1

    replaced = upload(profile_api, headers, image_bytes("#880000", fmt="JPEG"),
                      content_type="image/jpeg")
    assert replaced.status_code == 200, replaced.text
    assert replaced.json()["avatar_version"] == 2

    # A new independent database session sees the stored bytes.
    with Session(postgres_schema) as db:
        stored = db.get(UserAvatar, first["user_id"])
        assert stored is not None
        assert stored.version == 2
        assert stored.mime_type == "image/jpeg"
        assert stored.image_data[:2] == bytes((0xFF, 0xD8))
        assert len(stored.image_data) <= 256 * 1024

    again = profile_api.get(f"{API}/profile/avatar", headers=headers)
    assert again.json()["avatar_version"] == 2
    assert again.json()["data_url"] != data_url

    # Re-create the API application and its SQL sessions (simulated API restart).
    restarted = FastAPI()
    restarted.include_router(profile_router.router, prefix=API)

    def independent_database():
        with Session(postgres_schema, expire_on_commit=False) as session:
            try:
                yield session
            except BaseException:
                session.rollback()
                raise

    restarted.dependency_overrides[profile_router._db_session] = independent_database
    with TestClient(restarted) as fresh_client:
        fresh_avatar = fresh_client.get(f"{API}/profile/avatar", headers=headers)
        assert fresh_avatar.status_code == 200, fresh_avatar.text
        assert fresh_avatar.json()["avatar_version"] == 2
        assert fresh_avatar.json()["data_url"] == again.json()["data_url"]
        assert fresh_client.get(
            f"{API}/profile", headers=headers
        ).json()["has_avatar"] is True

    deleted = profile_api.delete(f"{API}/profile/avatar", headers=headers)
    assert deleted.status_code == 204
    assert deleted.headers["cache-control"] == "no-store"
    assert profile_api.delete(
        f"{API}/profile/avatar", headers=headers
    ).status_code == 204
    assert profile_api.get(
        f"{API}/profile/avatar", headers=headers
    ).status_code == 404
    assert profile_api.get(
        f"{API}/profile", headers=headers
    ).json()["has_avatar"] is False
    with Session(postgres_schema) as db:
        assert db.get(UserAvatar, first["user_id"]) is None


def test_real_heic_codec_upload_is_normalized_in_postgres(
    profile_api, registered_users
):
    """Synthetic HEIC exercises libheif; a real iPhone 48MP file remains manual."""
    from pillow_heif import register_heif_opener

    register_heif_opener()
    output = BytesIO()
    Image.new("RGB", (1200, 900), "#135e73").save(
        output, format="HEIF", quality=70
    )
    assert 0 < output.tell() <= 5 * 1024 * 1024
    _, headers = registered_users[0]
    response = upload(profile_api, headers, output.getvalue(), "image/heic")
    assert response.status_code == 200, response.text
    saved = profile_api.get(f"{API}/profile/avatar", headers=headers)
    assert saved.status_code == 200
    result = base64.b64decode(saved.json()["data_url"].split(",", 1)[1])
    with Image.open(BytesIO(result)) as image:
        assert image.format == "JPEG"
        assert max(image.size) <= 512
