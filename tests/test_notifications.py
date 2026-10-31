import datetime as dt

import pytest
from sqlalchemy import select, func

from backend.app.core.clock import today_local
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.notification import Notification
from backend.app.services.notifications import emit_relapse_once


def test_variant_changes_only_automatic_copy_and_keeps_ownership(inbox):
    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    url=f"/api/v1/notifications/{notice.notification_id}"
    first=client.get(url+'?variant=0',headers=mh)
    second=client.get(url+'?variant=1',headers=mh)
    assert first.status_code == second.status_code == 200
    assert first.json()['body'] != second.json()['body']
    assert first.json()['notification_id'] == second.json()['notification_id']
    assert client.get(url+'?variant=1',headers=eh).status_code == 404
    assert client.get(url+'?variant=4',headers=mh).status_code == 422


@pytest.fixture
def inbox(authenticated_calendar, registered_users, calendar_db):
    from backend.app.routers.notifications import router

    authenticated_calendar.app.include_router(router, prefix="/api/v1")
    (mentor, mh), (mentee, eh) = registered_users
    relation = Mentorship(mentor_id=mentor["user_id"], mentee_id=mentee["user_id"])
    calendar_db.add(relation)
    calendar_db.flush()
    record = DayRecord(
        user_id=mentee["user_id"], date=today_local(), status="relapse", drinks=[]
    )
    calendar_db.add(record)
    calendar_db.flush()
    emit_relapse_once(calendar_db, record.record_id, None)
    calendar_db.commit()
    notice = calendar_db.scalar(
        select(Notification).where(Notification.kind == "relapse")
    )
    return (
        authenticated_calendar,
        calendar_db,
        mentor,
        mentee,
        mh,
        eh,
        relation,
        record,
        notice,
    )


def test_inbox_is_private_paginated_and_read_is_idempotent(inbox):
    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    page = client.get("/api/v1/notifications?limit=1&offset=0", headers=mh)
    assert page.status_code == 200, page.text
    assert page.headers["cache-control"] == "no-store"
    responses = client.app.openapi()["paths"][
        "/api/v1/notifications/{notification_id}/support"
    ]["post"]["responses"]
    assert {"201", "401", "403", "404", "409", "422"}.issubset(responses)
    assert page.json()["total"] == 1
    assert page.json()["items"][0]["can_support"] is True
    assert client.get("/api/v1/notifications/unread-count", headers=mh).json() == {
        "count": 1
    }
    url = f"/api/v1/notifications/{notice.notification_id}"
    assert client.get(url, headers=eh).status_code == 404
    assert client.patch(url + "/read", headers=eh).status_code == 404
    first = client.patch(url + "/read", headers=mh)
    second = client.patch(url + "/read", headers=mh)
    assert first.status_code == 200, first.text
    assert first.json()["read_at"] == second.json()["read_at"]
    assert client.get("/api/v1/notifications/unread-count", headers=mh).json() == {
        "count": 0
    }
    assert client.get("/api/v1/notifications?limit=101", headers=mh).status_code == 422
    assert client.get("/api/v1/notifications").status_code == 401


def test_relapse_is_emitted_only_once_even_after_status_cycles(inbox):
    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    for previous, status in [
        ("relapse", "sober"),
        ("sober", "relapse"),
        ("relapse", "relapse"),
    ]:
        record.status = status
        db.flush()
        emit_relapse_once(db, record.record_id, previous)
    db.commit()
    assert db.scalar(select(func.count()).select_from(Notification)) == 1


def test_first_relapse_without_mentor_is_not_replayed(calendar_db, registered_users):
    (_, _), (account, _) = registered_users
    record = DayRecord(
        user_id=account["user_id"], date=today_local(), status="relapse", drinks=[]
    )
    calendar_db.add(record)
    calendar_db.flush()
    emit_relapse_once(calendar_db, record.record_id, None)
    calendar_db.commit()
    calendar_db.add(
        Mentorship(
            mentor_id=registered_users[0][0]["user_id"], mentee_id=account["user_id"]
        )
    )
    calendar_db.flush()
    record.status = "sober"
    calendar_db.flush()
    record.status = "relapse"
    calendar_db.flush()
    emit_relapse_once(calendar_db, record.record_id, "sober")
    calendar_db.commit()
    assert calendar_db.scalar(select(func.count()).select_from(Notification)) == 0
    calendar_db.refresh(record)
    assert record.first_relapse_at is not None


def test_rollback_removes_marker_and_notification(calendar_db, registered_users):
    mentor, mentee = [item[0]["user_id"] for item in registered_users]
    calendar_db.add(Mentorship(mentor_id=mentor, mentee_id=mentee))
    record = DayRecord(user_id=mentee, date=today_local(), status="sober", drinks=[])
    calendar_db.add(record)
    calendar_db.commit()
    record_id = record.record_id
    record.status = "relapse"
    calendar_db.flush()
    emit_relapse_once(calendar_db, record_id, "sober")
    calendar_db.rollback()
    calendar_db.refresh(record)
    assert record.status == "sober" and record.first_relapse_at is None
    assert calendar_db.scalar(select(func.count()).select_from(Notification)) == 0


def test_parallel_first_events_have_one_marker_and_notice(
    calendar_db, registered_users, postgres_schema
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    from backend.app.db.models.user import User

    mentor, mentee = [item[0]["user_id"] for item in registered_users]
    relation = Mentorship(mentor_id=mentor, mentee_id=mentee)
    record = DayRecord(user_id=mentee, date=today_local(), status="sober", drinks=[])
    calendar_db.add_all([relation, record])
    calendar_db.commit()
    record_id = record.record_id
    barrier = Barrier(2)

    def emit():
        with Session(postgres_schema) as db:
            barrier.wait(timeout=10)
            db.scalar(select(User).where(User.user_id == mentee).with_for_update())
            db.scalar(
                select(Mentorship)
                .where(Mentorship.relationship_id == relation.relationship_id)
                .with_for_update()
            )
            entry = db.scalar(
                select(DayRecord)
                .where(DayRecord.record_id == record_id)
                .with_for_update()
            )
            previous = entry.status
            entry.status = "relapse"
            db.flush()
            emit_relapse_once(db, record_id, previous)
            db.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(emit) for _ in range(2)]
        for job in jobs:
            job.result(timeout=20)
    assert calendar_db.scalar(select(func.count()).select_from(Notification)) == 1
    calendar_db.refresh(record)
    assert record.first_relapse_at is not None
