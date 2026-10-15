"""Тести статистики тверезості для КТ-5."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from backend.app import stubs
from backend.app.main import app
from backend.app.models import DayStatus, EntryOut
from backend.app.services.statistics import (
    calculate_statistics,
    count_streaks,
    get_goal_progress,
)

client = TestClient(app)

HEADERS = {"Authorization": "Bearer user-42"}
STATISTICS_URL = "/api/v1/statistics"
ENTRIES_URL = "/api/v1/calendar/entries"


@pytest.fixture(autouse=True)
def reset_data():
    """Відновлює демонстраційні дані перед і після кожного тесту."""

    stubs.reset()
    yield
    stubs.reset()


def make_entry(
    entry_date: dt.date,
    status: DayStatus = DayStatus.relapse,
    user_id: int = 42,
) -> EntryOut:
    """Створює календарний запис для тестування розрахунків."""

    return EntryOut(
        record_id=100,
        user_id=user_id,
        date=entry_date,
        status=status,
        trigger_category=None,
        created_at=dt.datetime.now(dt.timezone.utc),
    )


def test_statistics_endpoint_returns_expected_fields():
    """API повертає всі поля погодженого контракту."""

    response = client.get(STATISTICS_URL, headers=HEADERS)

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "period",
        "tracking_start_date",
        "period_start",
        "period_end",
        "sober_days",
        "relapse_days",
        "total_sober_days",
        "current_streak",
        "longest_streak",
        "active_goal_days",
        "completed_goal_days",
        "goal_progress_days",
    }

    assert set(data) == expected_fields


def test_initial_statistics():
    """Стартові дані: 7 днів відстеження та один день вживання."""

    response = client.get(
        STATISTICS_URL,
        headers=HEADERS,
        params={"period": "all"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["period"] == "all"
    assert data["sober_days"] == 6
    assert data["relapse_days"] == 1
    assert data["total_sober_days"] == 6
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 5
    assert data["active_goal_days"] == 7
    assert data["completed_goal_days"] == []
    assert data["goal_progress_days"] == 6


def test_week_statistics():
    """Тиждень охоплює останні сім календарних днів."""

    response = client.get(
        STATISTICS_URL,
        headers=HEADERS,
        params={"period": "week"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["period"] == "week"
    assert data["sober_days"] == 6
    assert data["relapse_days"] == 1
    assert data["period_end"] == dt.date.today().isoformat()


@pytest.mark.parametrize("period", ["all", "week", "month", "year"])
def test_supported_periods(period):
    """Усі чотири погоджені періоди доступні через API."""

    response = client.get(
        STATISTICS_URL,
        headers=HEADERS,
        params={"period": period},
    )

    assert response.status_code == 200
    assert response.json()["period"] == period


def test_invalid_period_returns_422():
    """Невідомий період відхиляється."""

    response = client.get(
        STATISTICS_URL,
        headers=HEADERS,
        params={"period": "decade"},
    )

    assert response.status_code == 422


def test_month_boundaries():
    """Місячна статистика починається з першого числа місяця."""

    today = dt.date(2026, 3, 2)
    tracking_start = dt.date(2026, 2, 25)

    result = calculate_statistics(
        tracking_start_date=tracking_start,
        today=today,
        entries=[
            make_entry(dt.date(2026, 2, 28)),
            make_entry(dt.date(2026, 3, 1)),
        ],
        period="month",
    )

    assert result["period_start"] == dt.date(2026, 3, 1)
    assert result["period_end"] == today
    assert result["sober_days"] == 1
    assert result["relapse_days"] == 1


def test_year_boundaries():
    """Річна статистика не включає дні попереднього року."""

    today = dt.date(2026, 1, 3)
    tracking_start = dt.date(2025, 12, 29)

    result = calculate_statistics(
        tracking_start_date=tracking_start,
        today=today,
        entries=[
            make_entry(dt.date(2025, 12, 31)),
            make_entry(dt.date(2026, 1, 2)),
        ],
        period="year",
    )

    assert result["period_start"] == dt.date(2026, 1, 1)
    assert result["sober_days"] == 2
    assert result["relapse_days"] == 1


def test_current_and_longest_streak():
    """Зрив перериває серію, але не стирає попередній рекорд."""

    start = dt.date(2026, 10, 9)
    end = dt.date(2026, 10, 15)

    current, longest = count_streaks(
        start_date=start,
        end_date=end,
        relapse_dates=[dt.date(2026, 10, 14)],
    )

    assert current == 1
    assert longest == 5


def test_streak_without_relapses():
    """Без зривів поточна та найдовша серії однакові."""

    current, longest = count_streaks(
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 7),
        relapse_dates=[],
    )

    assert current == 7
    assert longest == 7


def test_streak_ends_on_relapse():
    """Якщо зрив відбувся сьогодні, поточна серія нульова."""

    current, longest = count_streaks(
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 4),
        relapse_dates=[dt.date(2026, 10, 4)],
    )

    assert current == 0
    assert longest == 3


@pytest.mark.parametrize(
    "days, expected_goal, expected_completed",
    [
        (0, 7, []),
        (6, 7, []),
        (7, 30, [7]),
        (29, 30, [7]),
        (30, None, [7, 30]),
        (40, None, [7, 30]),
    ],
)
def test_goal_progress(days, expected_goal, expected_completed):
    """Цілі автоматично переходять від 7 до 30 днів."""

    active, completed, progress = get_goal_progress(days)

    assert active == expected_goal
    assert completed == expected_completed
    assert progress == days


def test_goal_progress_rejects_negative_days():
    """Від'ємна кількість тверезих днів заборонена."""

    with pytest.raises(ValueError):
        get_goal_progress(-1)


def test_statistics_ignores_other_users_entries():
    """Записи іншого користувача не впливають на нашу статистику."""

    before = client.get(STATISTICS_URL, headers=HEADERS)

    assert before.status_code == 200

    other_entry = make_entry(
        entry_date=dt.date.today(),
        user_id=99,
    )
    other_entry = other_entry.model_copy(update={"record_id": 999})

    stubs.entries[999] = other_entry

    after = client.get(STATISTICS_URL, headers=HEADERS)

    assert after.status_code == 200
    assert after.json() == before.json()


def test_statistics_changes_after_new_entry():
    """Після POST календар і статистика відображають одні дані."""

    before = client.get(STATISTICS_URL, headers=HEADERS)

    assert before.status_code == 200
    assert before.json()["sober_days"] == 6

    today = dt.date.today().isoformat()

    created = client.post(
        ENTRIES_URL,
        headers=HEADERS,
        json={
            "date": today,
            "status": "relapse",
            "trigger_category": "social",
            "drinks": [
                {"type": "beer", "volume_ml": 330},
                {"type": "wine", "volume_ml": 150},
            ],
            "comment": "Перевірка статистики",
        },
    )

    assert created.status_code == 201

    calendar = client.get(
        ENTRIES_URL,
        headers=HEADERS,
        params={"from": today, "to": today},
    )

    assert calendar.status_code == 200
    assert calendar.json()["total"] == 1
    assert len(calendar.json()["items"][0]["drinks"]) == 2

    after = client.get(STATISTICS_URL, headers=HEADERS)

    assert after.status_code == 200

    data = after.json()

    assert data["sober_days"] == 5
    assert data["relapse_days"] == 2
    assert data["total_sober_days"] == 5
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 5
    assert data["goal_progress_days"] == 5


def test_statistics_without_tracking_start():
    """API повертає 404, якщо відстеження не розпочато."""

    stubs.tracking_start_dates.pop(42)

    response = client.get(STATISTICS_URL, headers=HEADERS)

    assert response.status_code == 404
    assert response.json()["code"] == "TRACKING_NOT_STARTED"
