"""System integration uses the real app, routers, JWT and PostgreSQL."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.core.clock import today_local, BUSINESS_TIMEZONE
from backend.app.db.models.user import User
from backend.app.db.models.complaint import Complaint
from backend.app.main import app
from backend.app import security


@pytest.fixture
def main_client(authenticated_calendar):
    previous = app.dependency_overrides.copy()
    app.dependency_overrides.update(authenticated_calendar.app.dependency_overrides)
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.mark.parametrize("path", ["/profile", "/mentorships/code", "/notifications"])
def test_new_private_modules_are_registered_and_protected(main_client, path):
    assert main_client.get("/api/v1" + path).status_code == 401


def test_full_relapse_support_complaint_flow(
    main_client, registered_users, calendar_db
):
    client, db = main_client, calendar_db
    (mentor, mh), (mentee, eh) = registered_users
    profile = client.get("/api/v1/profile", headers=eh)
    assert profile.status_code == 200, profile.text
    assert profile.json()["message_style"] == "formal"
    code = client.get("/api/v1/mentorships/code", headers=eh).json()["code"]
    joined = client.post("/api/v1/mentorships", headers=mh, json={"code": code})
    assert joined.status_code == 201, joined.text
    rid = joined.json()["relationship_id"]
    record = client.post(
        "/api/v1/calendar/entries",
        headers=eh,
        json={
            "date": today_local().isoformat(),
            "status": "relapse",
            "trigger_category": "stress",
            "drinks": [],
        },
    )
    assert record.status_code == 201, record.text
    inbox = client.get("/api/v1/notifications", headers=mh).json()
    assert inbox["total"] == 1
    notice_id = inbox["items"][0]["notification_id"]
    assert (
        client.get(f"/api/v1/mentorships/{rid}/statistics", headers=mh).status_code
        == 200
    )
    sent = client.post(
        f"/api/v1/notifications/{notice_id}/support",
        headers=mh,
        json={"text": "Ти впораєшся"},
    )
    assert sent.status_code == 201, sent.text
    received = client.get("/api/v1/notifications", headers=eh).json()["items"][0]
    evidence = received["support_comment"]["support_comment_id"]
    complaint = client.post(
        "/api/v1/complaints",
        headers=eh,
        json={
            "relationship_id": rid,
            "reason": "Test complaint",
            "support_comment_id": evidence,
        },
    )
    assert complaint.status_code == 201, complaint.text
    cid = complaint.json()["complaint_id"]
    db.expire_all()
    assert db.get(Complaint, cid).evidence_text == "Ти впораєшся"
    admin = User(
        name="Admin",
        nickname="admin",
        email="ktb-admin@example.test",
        password_hash="test-only",
        role="admin",
        tracking_start_date=today_local(),
    )
    db.add(admin)
    db.commit()
    ah = {
        "Authorization": "Bearer "
        + security.create_access_token(admin.user_id, admin.token_version)
    }
    response = client.patch(
        f"/api/v1/admin/complaints/{cid}", headers=ah, json={"decision": "approved"}
    )
    assert response.status_code == 200, response.text
    for suffix in ("calendar/entries", "statistics"):
        assert (
            client.get(f"/api/v1/mentorships/{rid}/{suffix}", headers=mh).status_code
            == 403
        )
    assert (
        client.post("/api/v1/mentorships", headers=mh, json={"code": code}).status_code
        == 403
    )
    assert client.get("/api/v1/auth/me", headers=mh).status_code == 200
    assert client.get("/api/v1/auth/me", headers=eh).status_code == 200
    assert client.get("/api/v1/notifications", headers=eh).json()["total"] == 1


def test_real_reminder_creator_is_connected_to_job(
    main_client, registered_users, calendar_db, postgres_schema, monkeypatch
):
    from backend.app.routers import jobs

    monkeypatch.setenv("REMINDERS_JOB_TOKEN", "ktb-job-secret-at-least-32-characters")
    for account, _ in registered_users:
        calendar_db.get(User, account["user_id"]).email_reminders_enabled = True
    calendar_db.commit()
    delivered = []

    class Sender:
        def send(self, address, subject, body):
            delivered.append(address)
            return "test-gmail-message"

    now = dt.datetime.combine(today_local(), dt.time(20), BUSINESS_TIMEZONE)
    app.dependency_overrides[jobs.get_engine_for_job] = lambda: postgres_schema
    app.dependency_overrides[jobs.get_clock] = lambda: lambda: now
    app.dependency_overrides[jobs.get_sender] = lambda: Sender()
    headers = {"X-Job-Token": "ktb-job-secret-at-least-32-characters"}
    response = main_client.post("/internal/jobs/reminders", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["created_in_app"] == 2
    assert response.json()["queued_email"] == 2
    assert response.json()["sent"] == 2
    assert len(delivered) == 2
    repeat = main_client.post("/internal/jobs/reminders", headers=headers)
    assert repeat.status_code == 200, repeat.text
    assert repeat.json()["created_in_app"] == repeat.json()["sent"] == 0
    assert len(delivered) == 2
