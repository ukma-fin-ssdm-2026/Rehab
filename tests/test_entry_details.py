"""Тести записів із напоями та коментарями для КТ-5."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from backend.app import stubs
from backend.app.main import app

client = TestClient(app)

HEADERS = {"Authorization": "Bearer user-42"}
URL = "/api/v1/calendar/entries"


@pytest.fixture(autouse=True)
def reset_data():
    """Відновлює тестові дані перед кожним тестом."""

    stubs.reset()
    yield
    stubs.reset()


def test_create_entry_with_one_drink():
    """Запис з одним напоєм успішно створюється."""

    response = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() - dt.timedelta(days=2)),
            "status": "relapse",
            "trigger_category": None,
            "drinks": [{"type": "beer", "volume_ml": 330}],
            "comment": "Один напій",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["drinks"] == [{"type": "beer", "volume_ml": 330}]
    assert data["comment"] == "Один напій"
    assert data["status"] == "relapse"


def test_create_entry_with_multiple_drinks():
    """Один календарний запис може містити кілька напоїв."""

    response = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() - dt.timedelta(days=2)),
            "status": "relapse",
            "trigger_category": "social",
            "drinks": [
                {"type": "beer", "volume_ml": 330},
                {"type": "wine", "volume_ml": 150},
            ],
            "comment": "Вечір із друзями",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert len(data["drinks"]) == 2
    assert data["drinks"][0]["type"] == "beer"
    assert data["drinks"][1]["type"] == "wine"
    assert data["drinks"][1]["volume_ml"] == 150
    assert data["comment"] == "Вечір із друзями"


def test_created_drinks_are_returned_by_get():
    """GET повертає напої, збережені через POST."""

    entry_date = str(dt.date.today() - dt.timedelta(days=2))

    created = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": entry_date,
            "status": "relapse",
            "drinks": [
                {"type": "cocktail", "volume_ml": 200},
                {"type": "other", "volume_ml": 50},
            ],
            "comment": "Перевірка GET",
        },
    )

    assert created.status_code == 201

    response = client.get(
        URL,
        headers=HEADERS,
        params={"from": entry_date, "to": entry_date},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert len(data["items"][0]["drinks"]) == 2
    assert data["items"][0]["comment"] == "Перевірка GET"


def test_old_entry_format_still_works():
    """Старі запити без drinks і comment залишаються сумісними."""

    response = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() - dt.timedelta(days=2)),
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["drinks"] == []
    assert data["comment"] is None


@pytest.mark.parametrize("volume", [0, -10, 1.5, "330"])
def test_invalid_drink_volume(volume):
    """Некоректний об'єм не приймається."""

    response = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() - dt.timedelta(days=2)),
            "status": "relapse",
            "drinks": [{"type": "beer", "volume_ml": volume}],
        },
    )

    assert response.status_code == 422


def test_invalid_drink_type():
    """Невідомий тип напою не приймається."""

    response = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() - dt.timedelta(days=2)),
            "status": "relapse",
            "drinks": [{"type": "unknown", "volume_ml": 200}],
        },
    )

    assert response.status_code == 422


def test_sober_day_cannot_contain_alcohol():
    """Тверезий день не може містити алкогольні напої."""

    response = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() - dt.timedelta(days=2)),
            "status": "sober",
            "drinks": [{"type": "wine", "volume_ml": 150}],
        },
    )

    assert response.status_code == 422


def test_duplicate_date_returns_conflict():
    """Другий запис на ту саму дату повертає 409."""

    payload = {
        "date": str(dt.date.today() - dt.timedelta(days=2)),
        "status": "relapse",
        "drinks": [{"type": "beer", "volume_ml": 330}],
    }

    first = client.post(URL, headers=HEADERS, json=payload)
    second = client.post(URL, headers=HEADERS, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_future_date_is_rejected():
    """Створення запису на майбутню дату заборонене."""

    response = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() + dt.timedelta(days=1)),
            "status": "relapse",
            "drinks": [{"type": "beer", "volume_ml": 330}],
        },
    )

    assert response.status_code == 422


def test_patch_to_sober_clears_drinks():
    """Зміна статусу на sober очищує список напоїв."""

    created = client.post(
        URL,
        headers=HEADERS,
        json={
            "date": str(dt.date.today() - dt.timedelta(days=2)),
            "status": "relapse",
            "drinks": [{"type": "beer", "volume_ml": 330}],
        },
    )

    assert created.status_code == 201
    record_id = created.json()["record_id"]

    updated = client.patch(
        f"{URL}/{record_id}",
        headers=HEADERS,
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "sober"
    assert updated.json()["drinks"] == []
