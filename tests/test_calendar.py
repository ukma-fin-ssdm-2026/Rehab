"""Тести календарного API та правила редагування протягом 48 годин."""

import pytest
import datetime as dt
from backend.app.repositories import entries as calendar_router
from backend.app.db.models.entry import DayRecord

API_URL = "/api/v1/calendar/entries"
AUTH_HEADERS = "owner"


def test_recent_entry_can_be_updated(calendar_regression_data):
    data = calendar_regression_data
    """Запис, створений годину тому, можна редагувати."""

    response = data.client.patch(
        f"{API_URL}/{data.recent_id}",
        headers=data.headers,
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["record_id"] == data.recent_id
    assert response.json()["status"] == "sober"
    assert response.json()["trigger_category"] is None


def test_old_entry_cannot_be_updated(calendar_regression_data):
    data = calendar_regression_data
    """Запис, створений п'ять днів тому, редагувати не можна."""

    response = data.client.patch(
        f"{API_URL}/{data.old_id}",
        headers=data.headers,
        json={
            "status": "relapse",
            "trigger_category": "stress",
        },
    )

    assert response.status_code == 403


def test_nonexistent_entry_returns_404(calendar_regression_data):
    data = calendar_regression_data
    """Неіснуючий запис повертає помилку 404."""

    response = data.client.patch(
        f"{API_URL}/999",
        headers=data.headers,
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 404


def test_other_users_entry_cannot_be_updated(calendar_regression_data):
    data = calendar_regression_data
    """Користувач не може редагувати чужий запис."""

    response = data.client.patch(
        f"{API_URL}/{data.recent_id}",
        headers=data.second_headers,
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 404


def test_update_requires_authorization(calendar_regression_data):
    data = calendar_regression_data

    response = data.client.patch(
        f"{API_URL}/{data.recent_id}",
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("elapsed", "headers", "payload", "expected_status"),
    [
        (
            dt.timedelta(hours=47, minutes=59, seconds=59),
            AUTH_HEADERS,
            {"status": "sober", "trigger_category": None},
            200,
        ),
        (
            dt.timedelta(hours=48),
            AUTH_HEADERS,
            {"status": "sober", "trigger_category": None},
            200,
        ),
        (
            dt.timedelta(hours=48, seconds=1),
            AUTH_HEADERS,
            {"status": "sober", "trigger_category": None},
            403,
        ),
        (
            dt.timedelta(hours=1),
            "other",
            {"status": "sober", "trigger_category": None},
            404,
        ),
        (
            dt.timedelta(hours=1),
            None,
            {"status": "sober", "trigger_category": None},
            401,
        ),
        (
            dt.timedelta(hours=1),
            AUTH_HEADERS,
            {
                "status": "sober",
                "trigger_category": None,
                "created_at": "2026-10-27T12:00:00Z",
            },
            422,
        ),
    ],
    ids=[
        "FR008-R1",
        "FR008-R2",
        "FR008-R3",
        "FR008-R4",
        "FR008-R5",
        "FR008-R6",
    ],
)
def test_fr008_decision_table(
    monkeypatch, elapsed, headers, payload, expected_status, calendar_regression_data
):
    data = calendar_regression_data
    headers = {"owner": data.headers, "other": data.second_headers}.get(headers)

    fixed_now = dt.datetime(2026, 10, 27, 12, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(calendar_router, "utc_now", lambda: fixed_now)

    original = data.db.get(DayRecord, data.recent_id)
    original.created_at = fixed_now - elapsed
    data.db.commit()
    before_edit = (original.status, original.trigger_category, original.created_at)

    response = data.client.patch(
        f"{API_URL}/{data.recent_id}",
        headers=headers,
        json=payload,
    )

    assert response.status_code == expected_status

    if expected_status == 200:
        assert response.json()["status"] == "sober"
        data.db.refresh(original)
        assert original.status == "sober"
        assert original.created_at == before_edit[2]
    else:
        data.db.refresh(original)
        assert (
            original.status,
            original.trigger_category,
            original.created_at,
        ) == before_edit

        expected_error_codes = {
            401: "UNAUTHORIZED",
            403: "EDIT_WINDOW_EXPIRED",
            404: "ENTRY_NOT_FOUND",
            422: "VALIDATION_ERROR",
        }

        assert response.json()["code"] == expected_error_codes[expected_status]


@pytest.mark.parametrize(
    ("forbidden_field", "value"),
    [
        ("date", "2026-10-20"),
        ("created_at", "2026-10-27T12:00:00Z"),
        ("user_id", 43),
    ],
)
def test_editing_rejects_forbidden_fields(
    forbidden_field, value, calendar_regression_data
):
    data = calendar_regression_data
    initial = data.db.get(DayRecord, data.recent_id)
    before = (initial.status, initial.created_at)

    response = data.client.patch(
        f"{API_URL}/{data.recent_id}",
        headers=data.headers,
        json={
            "status": "sober",
            "trigger_category": None,
            forbidden_field: value,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    data.db.refresh(initial)
    assert (initial.status, initial.created_at) == before


def test_editing_does_not_extend_original_window(monkeypatch, calendar_regression_data):
    data = calendar_regression_data
    fixed_time = dt.datetime(2026, 10, 27, 12, 0, tzinfo=dt.timezone.utc)
    initial = data.db.get(DayRecord, data.recent_id)
    original_created_at = fixed_time - dt.timedelta(hours=47)

    initial.created_at = original_created_at
    data.db.commit()

    monkeypatch.setattr(calendar_router, "utc_now", lambda: fixed_time)

    first_response = data.client.patch(
        f"{API_URL}/{data.recent_id}",
        headers=data.headers,
        json={"status": "sober", "trigger_category": None},
    )

    assert first_response.status_code == 200
    data.db.refresh(initial)
    after_first_edit = (initial.status, initial.trigger_category, initial.created_at)
    assert initial.created_at == original_created_at

    monkeypatch.setattr(
        calendar_router,
        "utc_now",
        lambda: fixed_time + dt.timedelta(hours=2),
    )

    second_response = data.client.patch(
        f"{API_URL}/{data.recent_id}",
        headers=data.headers,
        json={"status": "relapse", "trigger_category": "stress"},
    )

    assert second_response.status_code == 403
    assert second_response.json()["code"] == "EDIT_WINDOW_EXPIRED"
    data.db.refresh(initial)
    assert (
        initial.status,
        initial.trigger_category,
        initial.created_at,
    ) == after_first_edit
