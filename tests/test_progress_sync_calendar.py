"""Наскрізна перевірка реального перерахунку з календарного маршруту."""

import datetime as dt

from backend.app.core.clock import today_local
from backend.app.db.models.goal import Goal
from backend.app.db.models.user import User

URL = "/api/v1/calendar/entries"


def test_calendar_write_updates_streak_without_legacy_goal_rows(
    authenticated_calendar, registered_users, calendar_db
):
    account, headers = registered_users[0]
    user_id = account["user_id"]
    user = calendar_db.get(User, user_id)
    user.tracking_start_date = today_local() - dt.timedelta(days=6)
    calendar_db.commit()

    response = authenticated_calendar.post(
        URL,
        headers=headers,
        json={"date": today_local().isoformat(), "status": "sober"},
    )

    assert response.status_code == 201, response.text
    calendar_db.expire_all()
    user = calendar_db.get(User, user_id)
    assert user.best_streak == 7
    assert calendar_db.query(Goal).filter_by(user_id=user_id).count() == 0


def test_calendar_create_and_correction_refresh_statistics_and_milestones(
    authenticated_calendar, registered_users, calendar_db
):
    from backend.app.routers import goals, statistics

    authenticated_calendar.app.include_router(goals.router, prefix="/api/v1")
    authenticated_calendar.app.include_router(statistics.router, prefix="/api/v1")
    account, headers = registered_users[0]
    user = calendar_db.get(User, account["user_id"])
    user.tracking_start_date = today_local() - dt.timedelta(days=6)
    calendar_db.commit()
    response = authenticated_calendar.post(
        URL,
        headers=headers,
        json={"date": today_local().isoformat(), "status": "sober"},
    )
    assert response.status_code == 201, response.text
    record_id = response.json()["record_id"]

    def snapshot(streak, completed):
        response = authenticated_calendar.get("/api/v1/statistics", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["current_streak"] == streak
        assert data["completed_goal_days"] == completed
        milestones = authenticated_calendar.get("/api/v1/goals", headers=headers)
        assert milestones.status_code == 200, milestones.text
        for item in milestones.json()["items"]:
            assert item["is_achieved"] == (item["target_days"] in completed)
            assert item["progress_days"] == min(streak, item["target_days"])

    snapshot(7, [7])
    response = authenticated_calendar.patch(
        f"{URL}/{record_id}",
        headers=headers,
        json={"status": "relapse", "trigger_category": "stress"},
    )
    assert response.status_code == 200, response.text
    snapshot(0, [])
    response = authenticated_calendar.patch(
        f"{URL}/{record_id}",
        headers=headers,
        json={"status": "sober", "trigger_category": None},
    )
    assert response.status_code == 200, response.text
    snapshot(7, [7])
