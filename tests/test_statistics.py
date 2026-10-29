"""Тести статистики тверезості з PostgreSQL та чистих розрахунків."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from backend.app.core.clock import today_local
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.user import User
from backend.app.main import app
from backend.app.models import DayStatus, EntryOut, EntryCreate
from backend.app.repositories.goals import create_goal
from backend.app.repositories.entries import create_entry
from backend.app.security import CurrentUser, _db_session, get_current_user
from backend.app.services.statistics import (
    calculate_statistics,
    count_streaks,
    get_period_start,
)

client = TestClient(app)
HEADERS = {"Authorization": "Bearer integration-test"}
STATISTICS_URL = "/api/v1/statistics"


@pytest.fixture(autouse=True)
def reset_data(calendar_db, db_users):
    owner_id, _ = db_users
    today = today_local()
    account = calendar_db.get(User, owner_id)
    account.tracking_start_date = today - dt.timedelta(days=6)
    calendar_db.add(
        DayRecord(
            user_id=owner_id,
            date=today - dt.timedelta(days=1),
            status="relapse",
            trigger_category="stress",
            drinks=[],
        )
    )
    create_goal(calendar_db, owner_id, 30)
    calendar_db.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(owner_id, "user")
    app.dependency_overrides[_db_session] = lambda: calendar_db
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(_db_session, None)


def make_entry(
    entry_date: dt.date,
    status: DayStatus = DayStatus.relapse,
    user_id: int = 1,
) -> EntryOut:
    """Створює запис для перевірки чистих розрахунків."""

    return EntryOut(
        record_id=100,
        user_id=user_id,
        date=entry_date,
        status=status,
        trigger_category=None,
        created_at=dt.datetime.now(dt.timezone.utc),
    )


def test_statistics_endpoint_returns_expected_fields():
    response = client.get(STATISTICS_URL, headers=HEADERS)

    assert response.status_code == 200
    assert set(response.json()) == {
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
        "has_goals",
        "completed_goal_days",
        "goal_progress_days",
    }


def test_initial_statistics():
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
    assert data["active_goal_days"] == 30
    assert data["has_goals"] is True
    assert data["completed_goal_days"] == []
    assert data["goal_progress_days"] == 1


def test_week_statistics():
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
    assert data["period_end"] == today_local().isoformat()


@pytest.mark.parametrize("period", ["all", "week", "month", "year"])
def test_supported_periods(period):
    response = client.get(
        STATISTICS_URL,
        headers=HEADERS,
        params={"period": period},
    )

    assert response.status_code == 200
    assert response.json()["period"] == period


def test_invalid_period_returns_422():
    response = client.get(
        STATISTICS_URL,
        headers=HEADERS,
        params={"period": "decade"},
    )

    assert response.status_code == 422


def test_get_period_start_rejects_invalid_period():
    with pytest.raises(ValueError, match="Невідомий період статистики"):
        get_period_start(
            period="decade",
            tracking_start_date=dt.date(2026, 10, 1),
            today=dt.date(2026, 10, 22),
        )


def test_month_boundaries():
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
    current, longest = count_streaks(
        start_date=dt.date(2026, 10, 9),
        end_date=dt.date(2026, 10, 15),
        relapse_dates=[dt.date(2026, 10, 14)],
    )

    assert current == 1
    assert longest == 5


def test_streak_without_relapses():
    current, longest = count_streaks(
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 7),
        relapse_dates=[],
    )

    assert current == 7
    assert longest == 7


def test_streak_ends_on_relapse():
    current, longest = count_streaks(
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 4),
        relapse_dates=[dt.date(2026, 10, 4)],
    )

    assert current == 0
    assert longest == 3


def test_streak_rejects_end_date_before_start_date():
    with pytest.raises(ValueError, match="Кінцева дата не може бути раніше початкової"):
        count_streaks(
            start_date=dt.date(2026, 10, 15),
            end_date=dt.date(2026, 10, 14),
            relapse_dates=[],
        )


def test_statistics_ignores_other_users_entries(calendar_db, db_users):
    before = client.get(STATISTICS_URL, headers=HEADERS)
    assert before.status_code == 200

    create_entry(
        calendar_db,
        db_users[1],
        EntryCreate(date=today_local(), status=DayStatus.relapse),
    )
    calendar_db.commit()

    after = client.get(STATISTICS_URL, headers=HEADERS)
    assert after.status_code == 200
    assert after.json() == before.json()


def test_statistics_recomputes_after_database_entry(calendar_db, db_users):
    before = client.get(STATISTICS_URL, headers=HEADERS)
    assert before.status_code == 200
    assert before.json()["sober_days"] == 6

    create_entry(
        calendar_db,
        db_users[0],
        EntryCreate(
            date=today_local(),
            status=DayStatus.relapse,
            trigger_category="social",
            drinks=[
                {"type": "beer", "volume_ml": 330},
                {"type": "wine", "volume_ml": 150},
            ],
            comment="Перевірка статистики",
        ),
    )
    calendar_db.commit()

    after = client.get(STATISTICS_URL, headers=HEADERS)
    assert after.status_code == 200
    data = after.json()
    assert data["sober_days"] == 5
    assert data["relapse_days"] == 2
    assert data["total_sober_days"] == 5
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 5
    assert data["goal_progress_days"] == 0


def test_calculate_statistics_rejects_invalid_period():
    with pytest.raises(ValueError, match="Невідомий період статистики"):
        calculate_statistics(
            tracking_start_date=dt.date(2026, 10, 1),
            today=dt.date(2026, 10, 22),
            entries=[],
            period="decade",
        )


def test_calculate_statistics_rejects_future_tracking_start():
    with pytest.raises(
        ValueError,
        match="Дата початку відстеження не може бути в майбутньому",
    ):
        calculate_statistics(
            tracking_start_date=dt.date(2026, 10, 23),
            today=dt.date(2026, 10, 22),
            entries=[],
            period="all",
        )


def test_statistics_without_tracking_start(calendar_db, db_users):
    account = calendar_db.get(User, db_users[0])
    calendar_db.delete(account)
    calendar_db.commit()

    response = client.get(STATISTICS_URL, headers=HEADERS)

    assert response.status_code == 404
    assert response.json()["code"] == "TRACKING_NOT_STARTED"
