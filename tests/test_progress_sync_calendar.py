"""Наскрізна перевірка реального перерахунку з календарного маршруту."""

import datetime as dt

from backend.app.core.clock import today_local
from backend.app.db.models.goal import Goal
from backend.app.db.models.user import User
from backend.app.repositories.goals import create_goal


URL = "/api/v1/calendar/entries"


def test_calendar_write_recomputes_goal_progress_in_same_transaction(
    authenticated_calendar, registered_users, calendar_db
):
    account, headers = registered_users[0]
    user_id = account["user_id"]
    user = calendar_db.get(User, user_id)
    user.tracking_start_date = today_local() - dt.timedelta(days=6)
    create_goal(calendar_db, user_id, 7)
    calendar_db.commit()

    response = authenticated_calendar.post(
        URL,
        headers=headers,
        json={"date": today_local().isoformat(), "status": "sober"},
    )

    assert response.status_code == 201, response.text
    calendar_db.expire_all()
    user = calendar_db.get(User, user_id)
    goal = calendar_db.query(Goal).filter_by(user_id=user_id).one()
    assert user.best_streak == 7
    assert goal.is_achieved is True
