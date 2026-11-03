import datetime as dt

import pytest
from sqlalchemy import select, func

from tests.test_auth_main_postgres import main_api, register, login  # noqa: F401
from backend.app.core.clock import today_local
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.notification import Notification
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.user import User

API = "/api/v1"


def setup_pair(client, db):
    mentor = register(client, "flow-mentor@example.test")
    mentee = register(client, "flow-mentee@example.test")
    relation = Mentorship(mentor_id=mentor["user_id"], mentee_id=mentee["user_id"])
    db.add(relation)
    db.get(User, mentee["user_id"]).tracking_start_date = today_local() - dt.timedelta(
        days=6
    )
    db.commit()
    return (
        mentor,
        mentee,
        login(client, mentor["email"]),
        login(client, mentee["email"]),
    )


def test_main_calendar_notification_support_and_progress_flow(main_api, calendar_db):
    client = main_api
    mentor, mentee, mh, eh = setup_pair(client, calendar_db)
    profile = client.get(API + "/profile", headers=mh)
    assert profile.status_code == 200, profile.text
    assert (
        client.patch(
            API + "/profile/preferences", headers=mh, json={"message_style": "zen"}
        ).status_code
        == 200
    )
    response = client.post(
        API + "/calendar/entries",
        headers=eh,
        json={"date": today_local().isoformat(), "status": "sober"},
    )
    assert response.status_code == 201, response.text
    record_id = response.json()["record_id"]
    assert client.get(API + "/statistics", headers=eh).json()[
        "completed_goal_days"
    ] == [7]
    assert client.get(API + "/notifications", headers=mh).json()["total"] == 0
    url = f"{API}/calendar/entries/{record_id}"
    assert (
        client.patch(
            url, headers=eh, json={"status": "relapse", "trigger_category": "stress"}
        ).status_code
        == 200
    )
    stats = client.get(API + "/statistics", headers=eh).json()
    assert stats["current_streak"] == 0 and stats["completed_goal_days"] == []
    notices = client.get(API + "/notifications", headers=mh).json()
    assert notices["total"] == 1
    notice = notices["items"][0]
    assert notice["title"] == "Будьте поруч"
    notice_url = f"{API}/notifications/{notice['notification_id']}"
    assert client.get(notice_url, headers=eh).status_code == 404
    result = client.post(notice_url + "/support", headers=mh, json={"text": "Я поруч"})
    assert result.status_code == 201, result.text
    child = client.get(API + "/notifications", headers=eh).json()["items"][0]
    assert child["support_comment"]["text"] == "Я поруч"
    assert child["can_report_mentor"] is True
    assert (
        client.patch(
            f"{API}/notifications/{child['notification_id']}/read", headers=eh
        ).status_code
        == 200
    )
    assert (
        client.get(API + "/notifications/unread-count", headers=eh).json()["count"] == 0
    )
    assert client.patch(url, headers=eh, json={"status": "sober"}).status_code == 200
    assert client.get(API + "/statistics", headers=eh).json()[
        "completed_goal_days"
    ] == [7]
    assert (
        client.get(notice_url, headers=mh).json()["support_comment"]["text"]
        == "Я поруч"
    )
    assert client.patch(url, headers=eh, json={"status": "relapse"}).status_code == 200
    assert client.get(API + "/notifications", headers=mh).json()["total"] == 1


def test_event_failure_rolls_back_calendar_progress_and_notification(
    main_api, calendar_db, monkeypatch
):
    from backend.app.routers import calendar_postgres

    client = main_api
    mentor, mentee, mh, eh = setup_pair(client, calendar_db)
    original = calendar_postgres.emit_relapse_once

    def failing(db, record_id, previous_status):
        original(db, record_id, previous_status)
        raise RuntimeError("simulated event failure")

    monkeypatch.setattr(calendar_postgres, "emit_relapse_once", failing)
    with pytest.raises(RuntimeError, match="simulated event failure"):
        client.post(
            API + "/calendar/entries",
            headers=eh,
            json={"date": today_local().isoformat(), "status": "relapse"},
        )
    assert calendar_db.scalar(select(func.count()).select_from(DayRecord)) == 0
    assert calendar_db.scalar(select(func.count()).select_from(Notification)) == 0
    calendar_db.expire_all()
    assert calendar_db.get(User, mentee["user_id"]).best_streak == 0
