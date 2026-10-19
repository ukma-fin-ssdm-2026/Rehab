"""Тести календарного API та правила редагування протягом 48 годин."""

import pytest
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
