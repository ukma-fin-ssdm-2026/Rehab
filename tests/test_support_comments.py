from sqlalchemy import select, func
from tests.test_notifications import inbox  # noqa: F401
from backend.app.db.models.notification import Notification
from backend.app.db.models.support_comment import SupportComment
from backend.app.services.mentorship import end_relationship


def test_support_is_plain_immutable_and_visible_to_its_recipient(inbox):
    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    url = f"/api/v1/notifications/{notice.notification_id}/support"
    assert client.post(url, headers=eh, json={"text": "wrong owner"}).status_code == 404
    response = client.post(url, headers=mh, json={"text": "  <b>Я поруч</b>  "})
    assert response.status_code == 201, response.text
    assert response.json()["text"] == "<b>Я поруч</b>"
    assert client.post(url, headers=mh, json={"text": "duplicate"}).status_code == 409
    page = client.get("/api/v1/notifications", headers=eh).json()
    assert page["total"] == 1
    child = page["items"][0]
    assert child["support_comment"]["text"] == "<b>Я поруч</b>"
    assert child["can_report_mentor"] is True
    assert (
        client.get(
            f"/api/v1/notifications/{child['notification_id']}", headers=mh
        ).status_code
        == 404
    )
    assert db.scalar(select(func.count()).select_from(SupportComment)) == 1
    end_relationship(db, relation.relationship_id, mentee["user_id"], "mentee_left")
    db.commit()
    old = client.get(
        f"/api/v1/notifications/{notice.notification_id}", headers=mh
    ).json()
    assert old["can_support"] is False and old["can_view_mentee"] is False
    assert old["support_comment"]["text"] == "<b>Я поруч</b>"
    assert (
        client.post(url, headers=mh, json={"text": "no longer allowed"}).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/notifications/{child['notification_id']}", headers=eh
        ).json()["can_report_mentor"]
        is True
    )


def test_corrected_sober_record_disables_new_support_and_keeps_event(inbox):
    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    record.status = "sober"
    db.commit()
    detail = client.get(
        f"/api/v1/notifications/{notice.notification_id}", headers=mh
    ).json()
    assert detail["can_support"] is False
    assert "тверез" in detail["body"], ascii(detail["body"])
    result = client.post(
        f"/api/v1/notifications/{notice.notification_id}/support",
        headers=mh,
        json={"text": "hello"},
    )
    assert (
        result.status_code == 409
        and result.json()["code"] == "RELAPSE_NO_LONGER_ACTIVE"
    )


def test_current_recipient_style_changes_copy_without_changing_support(inbox):
    from backend.app.db.models.user import User

    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    url = f"/api/v1/notifications/{notice.notification_id}"
    original = client.get(url, headers=mh).json()
    db.get(User, mentor["user_id"]).message_style = "zen"
    db.commit()
    changed = client.get(url, headers=mh).json()
    assert changed["title"] != original["title"]
    assert changed["notification_id"] == original["notification_id"]


def test_simultaneous_support_creates_one_comment(inbox, postgres_schema):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    from fastapi import HTTPException
    from backend.app.services.notifications import send_support

    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    barrier = Barrier(2)

    def send():
        with Session(postgres_schema) as session:
            barrier.wait(timeout=10)
            try:
                send_support(
                    session, mentor["user_id"], notice.notification_id, "Я поруч"
                )
                session.commit()
                return 201
            except HTTPException as error:
                session.rollback()
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(send) for _ in range(2)]
        assert sorted(job.result(timeout=20) for job in jobs) == [201, 409]
    assert db.scalar(select(func.count()).select_from(SupportComment)) == 1
    assert (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.kind == "support_comment")
        )
        == 1
    )


def test_support_racing_with_end_keeps_access_closed(inbox, postgres_schema):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    from fastapi import HTTPException
    from backend.app.services.notifications import send_support

    client, db, mentor, mentee, mh, eh, relation, record, notice = inbox
    barrier = Barrier(2)

    def send():
        with Session(postgres_schema) as session:
            barrier.wait(timeout=10)
            try:
                send_support(
                    session, mentor["user_id"], notice.notification_id, "Я поруч"
                )
                session.commit()
                return 201
            except HTTPException as error:
                session.rollback()
                return error.status_code

    def end():
        with Session(postgres_schema) as session:
            barrier.wait(timeout=10)
            end_relationship(
                session, relation.relationship_id, mentee["user_id"], "mentee_left"
            )
            session.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(send)
        second = pool.submit(end)
        assert first.result(timeout=20) in (201, 403)
        second.result(timeout=20)
    detail = client.get(
        f"/api/v1/notifications/{notice.notification_id}", headers=mh
    ).json()
    assert detail["can_support"] is False and detail["can_view_mentee"] is False
