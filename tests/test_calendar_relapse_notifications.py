"""Calendar writes and notification creation share a real SQL transaction."""

import datetime as dt

import pytest
from sqlalchemy import select, func

from backend.app.core.clock import today_local
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.notification import Notification
from backend.app.db.models.user import User

CALENDAR = "/api/v1/calendar/entries"


@pytest.fixture
def flow(authenticated_calendar, registered_users, calendar_db):
    from backend.app.routers import mentorship, notifications

    for module in (mentorship, notifications):
        authenticated_calendar.app.include_router(module.router, prefix="/api/v1")
    (mentor, mh), (mentee, eh) = registered_users
    response = authenticated_calendar.post(
        "/api/v1/mentorships",
        headers=mh,
        json={"code": calendar_db.get(User, mentee["user_id"]).mentor_code},
    )
    assert response.status_code == 201, response.text
    return (
        authenticated_calendar,
        calendar_db,
        mh,
        eh,
        response.json()["relationship_id"],
    )


def write(client, headers, status, record_id=None):
    payload = {
        "status": status,
        "trigger_category": "stress" if status == "relapse" else None,
    }
    if record_id is None:
        return client.post(
            CALENDAR,
            headers=headers,
            json={**payload, "date": today_local().isoformat()},
        )
    return client.patch(f"{CALENDAR}/{record_id}", headers=headers, json=payload)


def test_calendar_emits_once_and_support_reaches_mentee(flow):
    client, db, mh, eh, rid = flow
    created = write(client, eh, "sober")
    assert created.status_code == 201, created.text
    record_id = created.json()["record_id"]
    for status in ("relapse", "relapse", "sober", "relapse"):
        response = write(client, eh, status, record_id)
        assert response.status_code == 200, response.text
    inbox = client.get("/api/v1/notifications", headers=mh).json()
    assert inbox["total"] == 1, inbox
    notice = inbox["items"][0]
    response = client.post(
        f"/api/v1/notifications/{notice['notification_id']}/support",
        headers=mh,
        json={"text": "Тримайся!"},
    )
    assert response.status_code == 201, response.text
    received = client.get("/api/v1/notifications", headers=eh).json()
    assert received["total"] == 1
    assert received["items"][0]["support_comment"]["text"] == "Тримайся!"


def test_first_relapse_without_mentor_is_marked_and_not_replayed(
    authenticated_calendar, registered_users, calendar_db
):
    client, db = authenticated_calendar, calendar_db
    (mentor, _), (mentee, eh) = registered_users
    response = write(client, eh, "relapse")
    assert response.status_code == 201, response.text
    record_id = response.json()["record_id"]
    db.expire_all()
    assert db.get(DayRecord, record_id).first_relapse_at is not None
    db.add(Mentorship(mentor_id=mentor["user_id"], mentee_id=mentee["user_id"]))
    db.commit()
    assert write(client, eh, "sober", record_id).status_code == 200
    assert write(client, eh, "relapse", record_id).status_code == 200
    assert db.scalar(select(func.count()).select_from(Notification)) == 0


def test_notification_failure_rolls_back_calendar_and_progress(flow, monkeypatch):
    client, db, mh, eh, rid = flow
    from backend.app.routers import calendar_postgres
    from backend.app.services.notifications import emit_relapse_once

    def fail_after_emit(session, record_id, previous_status):
        emit_relapse_once(session, record_id, previous_status)
        raise RuntimeError("injected notification failure")

    monkeypatch.setattr(
        calendar_postgres, "emit_relapse_once", fail_after_emit, raising=False
    )
    with pytest.raises(RuntimeError, match="injected notification failure"):
        write(client, eh, "relapse")
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(DayRecord)) == 0
    assert db.scalar(select(func.count()).select_from(Notification)) == 0


def test_corrected_record_disables_support_and_expired_edit_emits_nothing(flow):
    client, db, mh, eh, rid = flow
    created = write(client, eh, "relapse")
    assert created.status_code == 201
    record_id = created.json()["record_id"]
    notices = client.get("/api/v1/notifications", headers=mh).json()["items"]
    assert len(notices) == 1
    assert write(client, eh, "sober", record_id).status_code == 200
    response = client.post(
        f"/api/v1/notifications/{notices[0]['notification_id']}/support",
        headers=mh,
        json={"text": "Support"},
    )
    assert response.status_code == 409
    db.expire_all()
    db.get(DayRecord, record_id).created_at -= dt.timedelta(hours=49)
    db.commit()
    assert write(client, eh, "relapse", record_id).status_code == 403
    assert db.scalar(select(func.count()).select_from(Notification)) == 1


def test_reminder_job_and_calendar_relapse_do_not_deadlock(
    calendar_db, db_users, postgres_schema
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from sqlalchemy import event, text
    from sqlalchemy.orm import Session
    from backend.app.core.clock import BUSINESS_TIMEZONE
    from backend.app.models import EntryCreate
    from backend.app.repositories.entries import create_entry, lock_calendar_owner
    from backend.app.services.notifications import emit_relapse_once
    from backend.app.services.reminders import create_due_reminders

    mentor, mentee = db_users
    calendar_db.add(Mentorship(mentor_id=mentor, mentee_id=mentee))
    calendar_db.commit()
    writer_ready, job_ready = Event(), Event()
    now = dt.datetime.combine(today_local(), dt.time(20), BUSINESS_TIMEZONE)

    def locked(conn, cursor, statement, parameters, context, executemany):
        if (
            conn.info.get("review_job")
            and "FOR" in statement
            and "users.user_id =" in statement
        ):
            if not job_ready.is_set():
                job_ready.set()
                assert writer_ready.wait(timeout=10)

    def calendar():
        with Session(postgres_schema) as session:
            session.execute(text("SET LOCAL lock_timeout='5s'"))
            lock_calendar_owner(session, mentee)
            writer_ready.set()
            assert job_ready.wait(timeout=10)
            row = create_entry(
                session,
                mentee,
                EntryCreate(
                    date=today_local(), status="relapse", trigger_category="stress"
                ),
            )
            emit_relapse_once(session, row.record_id, None)
            session.commit()

    def job():
        with Session(postgres_schema) as session:
            session.execute(text("SET LOCAL lock_timeout='5s'"))
            session.connection().info["review_job"] = True
            try:
                result = create_due_reminders(session, now)
                session.commit()
                return result
            finally:
                session.connection().info.pop("review_job", None)

    event.listen(postgres_schema, "after_cursor_execute", locked)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(calendar), pool.submit(job)]
            for future in futures:
                future.result(timeout=20)
    finally:
        event.remove(postgres_schema, "after_cursor_execute", locked)
    assert (
        calendar_db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.kind == "relapse")
        )
        == 1
    )
