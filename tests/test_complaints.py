# AI-GENERATED START
"""Скарги й адмінка (ТЗ С-1, С-2, С-5) на ізольованій PostgreSQL."""

import datetime as dt

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app import security
from backend.app.core.clock import BUSINESS_TIMEZONE
from backend.app.db.models.complaint import Complaint
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.notification import Notification
from backend.app.db.models.support_comment import SupportComment
from backend.app.db.models.user import User
from backend.app.main import http_exception_handler, validation_exception_handler
from backend.app.routers import admin, complaints
from backend.app.services.complaints import admin_overview, registration_window

SECRET = "complaints-test-secret-at-least-32-characters"
API = "/api/v1"


@pytest.fixture
def db(monkeypatch, calendar_db):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    yield calendar_db


@pytest.fixture
def client(db):
    app = FastAPI()
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(admin.router, prefix=API)
    app.include_router(complaints.router, prefix=API)
    app.dependency_overrides[security._db_session] = lambda: db
    return TestClient(app)


def make_user(db, nickname, role="user", **extra):
    user = User(
        name=nickname.title(),
        nickname=nickname,
        email=f"{nickname}@example.test",
        password_hash="test-only-hash",
        role=role,
        tracking_start_date=dt.date(2026, 1, 1),
        **extra,
    )
    db.add(user)
    db.commit()
    return user


def link(db, mentor, mentee, **extra):
    relationship = Mentorship(mentor_id=mentor.user_id, mentee_id=mentee.user_id)
    for key, value in extra.items():
        setattr(relationship, key, value)
    db.add(relationship)
    db.commit()
    return relationship


def support_comment(db, relationship, text="Тримайся, ти впораєшся"):
    relapse = Notification(
        recipient_id=relationship.mentor_id,
        sender_id=relationship.mentee_id,
        kind="relapse",
        event_key=f"relapse:{relationship.mentee_id}:2026-10-01",
        business_date=dt.date(2026, 10, 1),
        relationship_id=relationship.relationship_id,
    )
    db.add(relapse)
    db.flush()
    comment = SupportComment(
        relationship_id=relationship.relationship_id,
        relapse_notification_id=relapse.notification_id,
        author_id=relationship.mentor_id,
        recipient_id=relationship.mentee_id,
        text=text,
    )
    db.add(comment)
    db.commit()
    return comment


def auth(user):
    token = security.create_access_token(user.user_id, user.token_version)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pair(db):
    mentor = make_user(db, "mentor")
    mentee = make_user(db, "mentee")
    return mentor, mentee, link(db, mentor, mentee)


@pytest.fixture
def admin_user(db):
    return make_user(db, "admin", role="admin")


def submit(client, user, relationship, **extra):
    body = {"relationship_id": relationship.relationship_id, "reason": " Грубо "}
    body.update(extra)
    return client.post(f"{API}/complaints", json=body, headers=auth(user))


def test_mentee_files_complaint_and_reported_is_derived(client, db, pair):
    mentor, mentee, relationship = pair

    response = submit(client, mentee, relationship)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending" and body["reason"] == "Грубо"
    stored = db.get(Complaint, body["complaint_id"])
    assert (stored.reporter_id, stored.reported_id) == (
        mentee.user_id,
        mentor.user_id,
    )
    assert db.get(Mentorship, relationship.relationship_id).status == "active"


def test_mentor_and_outsider_cannot_file(client, db, pair):
    mentor, _, relationship = pair
    outsider = make_user(db, "outsider")

    assert submit(client, mentor, relationship).status_code == 403
    assert submit(client, outsider, relationship).status_code == 404
    assert db.scalar(select(Complaint.complaint_id)) is None


@pytest.mark.parametrize(
    "extra", [{"reason": "   "}, {"reason": "x" * 2001}, {"reported_id": 1}]
)
def test_invalid_payload_is_rejected(client, pair, extra):
    _, mentee, relationship = pair

    assert submit(client, mentee, relationship, **extra).status_code == 422


def test_comment_evidence_is_snapshotted(client, db, pair):
    _, mentee, relationship = pair
    comment = support_comment(db, relationship)

    response = submit(
        client, mentee, relationship, support_comment_id=comment.support_comment_id
    )

    assert response.status_code == 201, response.text
    stored = db.get(Complaint, response.json()["complaint_id"])
    assert stored.evidence_text == "Тримайся, ти впораєшся"
    assert stored.evidence_created_at == comment.created_at


def test_foreign_comment_is_not_accepted_as_evidence(client, db, pair):
    _, mentee, relationship = pair
    other_mentor = make_user(db, "other-mentor")
    other_mentee = make_user(db, "other-mentee")
    foreign = support_comment(db, link(db, other_mentor, other_mentee), "чуже")

    response = submit(
        client, mentee, relationship, support_comment_id=foreign.support_comment_id
    )

    assert response.status_code == 404
    assert response.json()["code"] == "SUPPORT_COMMENT_NOT_FOUND"
    assert "чуже" not in response.text


def test_pending_duplicate_is_not_created(client, db, pair):
    _, mentee, relationship = pair
    assert submit(client, mentee, relationship).status_code == 201

    response = submit(client, mentee, relationship)

    assert response.status_code == 409
    assert response.json()["code"] == "COMPLAINT_ALREADY_PENDING"
    assert len(db.scalars(select(Complaint)).all()) == 1


def test_complaint_about_ended_relationship_is_allowed(client, db, pair):
    _, mentee, relationship = pair
    relationship.status = "ended"
    relationship.ended_at = dt.datetime.now(dt.timezone.utc)
    relationship.ended_by = mentee.user_id
    relationship.ended_reason = "mentee_left"
    db.commit()

    assert submit(client, mentee, relationship).status_code == 201


def decide(client, admin_user, complaint_id, decision):
    return client.patch(
        f"{API}/admin/complaints/{complaint_id}",
        json={"decision": decision},
        headers=auth(admin_user),
    )


def test_approval_ends_pair_and_repeat_is_idempotent(client, db, pair, admin_user):
    _, mentee, relationship = pair
    complaint_id = submit(client, mentee, relationship).json()["complaint_id"]

    first = decide(client, admin_user, complaint_id, "approved")
    repeat = decide(client, admin_user, complaint_id, "approved")
    opposite = decide(client, admin_user, complaint_id, "rejected")

    assert first.status_code == repeat.status_code == 200
    assert first.json()["reviewed_at"] == repeat.json()["reviewed_at"]
    assert opposite.status_code == 409
    assert opposite.json()["code"] == "COMPLAINT_ALREADY_REVIEWED"
    db.expire_all()
    ended = db.get(Mentorship, relationship.relationship_id)
    assert (ended.status, ended.ended_reason) == ("ended", "complaint")
    assert db.get(Complaint, complaint_id).reviewed_by == admin_user.user_id


def test_rejection_keeps_active_pair_and_does_not_restore_ended(
    client, db, pair, admin_user
):
    _, mentee, relationship = pair
    first = submit(client, mentee, relationship).json()["complaint_id"]

    assert decide(client, admin_user, first, "rejected").status_code == 200
    db.expire_all()
    assert db.get(Mentorship, relationship.relationship_id).status == "active"

    mentee_id = mentee.user_id
    relationship = db.get(Mentorship, relationship.relationship_id)
    relationship.status = "ended"
    relationship.ended_at = dt.datetime.now(dt.timezone.utc)
    relationship.ended_by = mentee_id
    relationship.ended_reason = "mentee_left"
    db.commit()
    second = submit(client, mentee, relationship).json()["complaint_id"]

    assert decide(client, admin_user, second, "rejected").status_code == 200
    db.expire_all()
    assert db.get(Mentorship, relationship.relationship_id).status == "ended"


def test_admin_list_shows_only_complaint_parties(client, db, pair, admin_user):
    mentor, mentee, relationship = pair
    make_user(db, "bystander")
    comment = support_comment(db, relationship)
    submit(client, mentee, relationship, support_comment_id=comment.support_comment_id)

    listed = client.get(f"{API}/admin/complaints", headers=auth(admin_user))

    assert listed.status_code == 200
    body = listed.json()
    assert (body["total"], body["limit"], body["offset"]) == (1, 30, 0)
    item = body["items"][0]
    assert item["reporter"] == {"nickname": "mentee", "email": "mentee@example.test"}
    assert item["reported"] == {"nickname": "mentor", "email": "mentor@example.test"}
    assert item["evidence"]["text"] == "Тримайся, ти впораєшся"
    assert "bystander" not in listed.text
    assert "mentor_code" not in listed.text and "password" not in listed.text
    detail = client.get(
        f"{API}/admin/complaints/{item['complaint_id']}", headers=auth(admin_user)
    )
    assert detail.json() == item


def test_admin_list_filters_by_status(client, db, pair, admin_user):
    _, mentee, relationship = pair
    complaint_id = submit(client, mentee, relationship).json()["complaint_id"]
    decide(client, admin_user, complaint_id, "rejected")

    def total(status):
        url = f"{API}/admin/complaints" + (f"?status={status}" if status else "")
        return client.get(url, headers=auth(admin_user)).json()["total"]

    assert (total(None), total("rejected"), total("approved"), total("all")) == (
        0,
        1,
        0,
        1,
    )
    bad = client.get(f"{API}/admin/complaints?status=x", headers=auth(admin_user))
    assert bad.status_code == 422


def test_unknown_complaint_returns_404(client, admin_user):
    response = client.get(f"{API}/admin/complaints/999", headers=auth(admin_user))

    assert response.status_code == 404
    assert response.json()["code"] == "COMPLAINT_NOT_FOUND"


def test_registration_window_uses_kyiv_day_boundaries():
    start, end = registration_window(dt.date(2026, 10, 30))

    assert start == dt.datetime(2026, 10, 1, tzinfo=BUSINESS_TIMEZONE)
    assert end == dt.datetime(2026, 10, 31, tzinfo=BUSINESS_TIMEZONE)
    # 2026-10-25 — перехід на зимовий час: зсув межі змінюється з +03 на +02.
    assert start.utcoffset() == dt.timedelta(hours=3)
    assert end.utcoffset() == dt.timedelta(hours=2)


def test_overview_counts_are_exact(db, admin_user):
    today = dt.date(2026, 10, 30)
    start, end = registration_window(today)
    first = make_user(db, "first", created_at=start)
    make_user(db, "too-early", created_at=start - dt.timedelta(microseconds=1))
    make_user(db, "too-late", created_at=end)
    make_user(db, "admin2", role="admin", created_at=start)
    legacy = make_user(db, "legacy", role="mentor", created_at=start)
    mentor = make_user(db, "busy-mentor", created_at=start)
    other = make_user(db, "other", created_at=start)
    link(db, mentor, first)
    link(db, mentor, other)
    link(
        db,
        legacy,
        mentor,
        status="ended",
        ended_at=dt.datetime.now(dt.timezone.utc),
        ended_by=legacy.user_id,
        ended_reason="mentor_left",
    )
    db.add(
        Complaint(
            relationship_id=db.scalar(select(Mentorship.relationship_id)),
            reporter_id=first.user_id,
            reported_id=mentor.user_id,
            reason="x",
        )
    )
    db.commit()

    overview = admin_overview(db, today)

    assert overview.registrations_last_30_days == 4
    assert overview.active_mentors == 1
    assert overview.active_relationships == 2
    assert overview.pending_complaints == 1
    assert overview.current_date == today


# AI-GENERATED END
