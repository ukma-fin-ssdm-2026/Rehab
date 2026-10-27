"""Тести календарного API та правила редагування протягом 48 годин."""

import pytest
import datetime as dt
from backend.app.routers import calendar as calendar_router
from fastapi.testclient import TestClient

from backend.app import stubs
from backend.app.main import app

client = TestClient(app)

API_URL = "/api/v1/calendar/entries"
AUTH_HEADERS = {"Authorization": "Bearer user-42"}


@pytest.fixture(autouse=True)
def reset_test_data():
    """Відновлює тестові записи до та після кожного тесту."""

    stubs.reset()
    yield
    stubs.reset()


def test_recent_entry_can_be_updated():
    """Запис, створений годину тому, можна редагувати."""

    response = client.patch(
        f"{API_URL}/2",
        headers=AUTH_HEADERS,
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["record_id"] == 2
    assert response.json()["status"] == "sober"
    assert response.json()["trigger_category"] is None


def test_old_entry_cannot_be_updated():
    """Запис, створений п'ять днів тому, редагувати не можна."""

    response = client.patch(
        f"{API_URL}/1",
        headers=AUTH_HEADERS,
        json={
            "status": "relapse",
            "trigger_category": "stress",
        },
    )

    assert response.status_code == 403


def test_nonexistent_entry_returns_404():
    """Неіснуючий запис повертає помилку 404."""

    response = client.patch(
        f"{API_URL}/999",
        headers=AUTH_HEADERS,
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 404


def test_other_users_entry_cannot_be_updated():
    """Користувач не може редагувати чужий запис."""

    response = client.patch(
        f"{API_URL}/2",
        headers={"Authorization": "Bearer user-43"},
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 404


def test_update_requires_authorization():
    """Для редагування запису потрібна авторизація."""

    response = client.patch(
        f"{API_URL}/2",
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("elapsed", "expected_status"),
    [
        (dt.timedelta(hours=47, minutes=59, seconds=59), 200),
        (dt.timedelta(hours=48), 200),
        (dt.timedelta(hours=48, seconds=1), 403),
    ],
)
def test_editing_at_48_hour_boundary(monkeypatch, elapsed, expected_status):

    fixed_now = dt.datetime(2026, 10, 27, 12, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(calendar_router, "utc_now", lambda: fixed_now)

    original = stubs.entries[2]
    stubs.entries[2] = original.model_copy(update={"created_at": fixed_now - elapsed})

    response = client.patch(
        f"{API_URL}/2",
        headers=AUTH_HEADERS,
        json={"status": "sober", "trigger_category": None},
    )

    assert response.status_code == expected_status

    if expected_status == 200:
        assert response.json()["status"] == "sober"
        assert stubs.entries[2].status.value == "sober"
    else:
        assert response.json()["code"] == "EDIT_WINDOW_EXPIRED"
        assert stubs.entries[2].status.value == "relapse"


@pytest.mark.parametrize(
    ("forbidden_field", "value"),
    [
        ("date", "2026-10-20"),
        ("created_at", "2026-10-27T12:00:00Z"),
        ("user_id", 43),
    ],
)
def test_editing_rejects_forbidden_fields(forbidden_field, value):
    initial = stubs.entries[2].model_copy(deep=True)

    response = client.patch(
        f"{API_URL}/2",
        headers=AUTH_HEADERS,
        json={
            "status": "sober",
            "trigger_category": None,
            forbidden_field: value,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert stubs.entries[2] == initial


def test_editing_does_not_extend_original_window(monkeypatch):
    fixed_time = dt.datetime(2026, 10, 27, 12, 0, tzinfo=dt.timezone.utc)
    initial = stubs.entries[2]
    original_created_at = fixed_time - dt.timedelta(hours=47)

    stubs.entries[2] = initial.model_copy(update={"created_at": original_created_at})

    monkeypatch.setattr(calendar_router, "utc_now", lambda: fixed_time)

    first_response = client.patch(
        f"{API_URL}/2",
        headers=AUTH_HEADERS,
        json={"status": "sober", "trigger_category": None},
    )

    assert first_response.status_code == 200
    after_first_edit = stubs.entries[2].model_copy(deep=True)
    assert after_first_edit.created_at == original_created_at

    monkeypatch.setattr(
        calendar_router,
        "utc_now",
        lambda: fixed_time + dt.timedelta(hours=2),
    )

    second_response = client.patch(
        f"{API_URL}/2",
        headers=AUTH_HEADERS,
        json={"status": "relapse", "trigger_category": "stress"},
    )

    assert second_response.status_code == 403
    assert second_response.json()["code"] == "EDIT_WINDOW_EXPIRED"
    assert stubs.entries[2] == after_first_edit
