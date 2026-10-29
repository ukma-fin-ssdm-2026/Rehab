"""Тести записів із напоями та коментарями для КТ-5."""

import datetime as dt

import pytest
from backend.app.core.clock import today_local

URL = "/api/v1/calendar/entries"


def test_create_entry_with_one_drink(calendar_regression_data):
    data = calendar_regression_data
    """Запис з одним напоєм успішно створюється."""

    response = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() - dt.timedelta(days=2)),
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


def test_create_entry_with_multiple_drinks(calendar_regression_data):
    data = calendar_regression_data
    """Один календарний запис може містити кілька напоїв."""

    response = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() - dt.timedelta(days=2)),
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


def test_created_drinks_are_returned_by_get(calendar_regression_data):
    data = calendar_regression_data
    """GET повертає напої, збережені через POST."""

    entry_date = str(today_local() - dt.timedelta(days=2))

    created = data.client.post(
        URL,
        headers=data.headers,
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

    response = data.client.get(
        URL,
        headers=data.headers,
        params={"from": entry_date, "to": entry_date},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert len(data["items"][0]["drinks"]) == 2
    assert data["items"][0]["comment"] == "Перевірка GET"


def test_old_entry_format_still_works(calendar_regression_data):
    data = calendar_regression_data
    """Старі запити без drinks і comment залишаються сумісними."""

    response = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() - dt.timedelta(days=2)),
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["drinks"] == []
    assert data["comment"] is None


@pytest.mark.parametrize("volume", [0, -10, 1.5, "330"])
def test_invalid_drink_volume(volume, calendar_regression_data):
    data = calendar_regression_data
    """Некоректний об'єм не приймається."""

    response = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() - dt.timedelta(days=2)),
            "status": "relapse",
            "drinks": [{"type": "beer", "volume_ml": volume}],
        },
    )

    assert response.status_code == 422


def test_invalid_drink_type(calendar_regression_data):
    data = calendar_regression_data
    """Невідомий тип напою не приймається."""

    response = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() - dt.timedelta(days=2)),
            "status": "relapse",
            "drinks": [{"type": "unknown", "volume_ml": 200}],
        },
    )

    assert response.status_code == 422


def test_sober_day_cannot_contain_alcohol(calendar_regression_data):
    data = calendar_regression_data
    """Тверезий день не може містити алкогольні напої."""

    response = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() - dt.timedelta(days=2)),
            "status": "sober",
            "drinks": [{"type": "wine", "volume_ml": 150}],
        },
    )

    assert response.status_code == 422


def test_duplicate_date_returns_conflict(calendar_regression_data):
    data = calendar_regression_data
    """Другий запис на ту саму дату повертає 409."""

    payload = {
        "date": str(today_local() - dt.timedelta(days=2)),
        "status": "relapse",
        "drinks": [{"type": "beer", "volume_ml": 330}],
    }

    first = data.client.post(URL, headers=data.headers, json=payload)
    second = data.client.post(URL, headers=data.headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_future_date_is_rejected(calendar_regression_data):
    data = calendar_regression_data
    """Створення запису на майбутню дату заборонене."""

    response = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() + dt.timedelta(days=1)),
            "status": "relapse",
            "drinks": [{"type": "beer", "volume_ml": 330}],
        },
    )

    assert response.status_code == 422


def test_patch_to_sober_clears_drinks(calendar_regression_data):
    data = calendar_regression_data
    """Зміна статусу на sober очищує список напоїв."""

    created = data.client.post(
        URL,
        headers=data.headers,
        json={
            "date": str(today_local() - dt.timedelta(days=2)),
            "status": "relapse",
            "drinks": [{"type": "beer", "volume_ml": 330}],
        },
    )

    assert created.status_code == 201
    record_id = created.json()["record_id"]

    updated = data.client.patch(
        f"{URL}/{record_id}",
        headers=data.headers,
        json={
            "status": "sober",
            "trigger_category": None,
        },
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "sober"
    assert updated.json()["drinks"] == []
