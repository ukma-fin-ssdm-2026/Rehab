# AI-GENERATED START
"""Поштова черга нагадувань і службовий job (ТЗ С-3, С-4, С-5).

Gmail замінено фейковим sender: у тестах і CI реальних листів немає.
"""

import datetime as dt
import threading

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.clock import BUSINESS_TIMEZONE
from backend.app.db.models.email_delivery import EmailReminderDelivery
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.notification import Notification
from backend.app.db.models.user import User
from backend.app.main import http_exception_handler, validation_exception_handler
from backend.app.routers import jobs
from backend.app.services import email_reminders
from backend.app.services.email_reminders import (
    SUBJECT,
    SendRejected,
    SendUncertain,
    build_message,
    deliver_pending_reminders,
)

TOKEN = "job-test-token-at-least-32-characters-long"
TODAY = dt.date(2026, 10, 30)
EVENING = dt.datetime(2026, 10, 30, 20, 15, tzinfo=BUSINESS_TIMEZONE)


class FakeSender:
    def __init__(self, outcomes=None):
        self.outcomes = list(outcomes or [])
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append((to, subject, body))
        outcome = self.outcomes.pop(0) if self.outcomes else "ok"
        if isinstance(outcome, Exception):
            raise outcome
        return f"gmail-{len(self.sent)}"


@pytest.fixture
def engine(calendar_db, postgres_schema):
    return postgres_schema


@pytest.fixture
def factory(engine):
    return lambda: Session(engine, expire_on_commit=False)


def make_user(db, nickname, opt_in=True, style="formal"):
    user = User(
        name=nickname,
        nickname=nickname,
        email=f"{nickname}@example.test",
        password_hash="test-only-hash",
        tracking_start_date=dt.date(2026, 10, 1),
        email_reminders_enabled=opt_in,
        message_style=style,
    )
    db.add(user)
    db.flush()
    return user


def queue(db, user, business_date=TODAY, **extra):
    notification = Notification(
        recipient_id=user.user_id,
        kind="daily_reminder",
        event_key=f"reminder:{business_date.isoformat()}",
        business_date=business_date,
    )
    db.add(notification)
    db.flush()
    delivery = EmailReminderDelivery(
        notification_id=notification.notification_id,
        recipient_id=user.user_id,
        business_date=business_date,
        **extra,
    )
    db.add(delivery)
    db.commit()
    return delivery.delivery_id


def status(factory, delivery_id):
    with factory() as db:
        return db.get(EmailReminderDelivery, delivery_id)


def test_opt_in_reminder_is_sent_once(calendar_db, factory):
    delivery_id = queue(calendar_db, make_user(calendar_db, "anna", style="zen"))
    sender = FakeSender()

    first = deliver_pending_reminders(factory, EVENING, sender)
    second = deliver_pending_reminders(factory, EVENING, sender)

    assert first == {"sent": 1, "skipped": 0, "failed": 0, "unknown": 0}
    assert second == {"sent": 0, "skipped": 0, "failed": 0, "unknown": 0}
    assert len(sender.sent) == 1
    to, subject, body = sender.sent[0]
    assert (to, subject) == ("anna@example.test", SUBJECT)
    assert "тверезий день" in body and "спокійно" in body
    row = status(factory, delivery_id)
    assert (row.status, row.provider_message_id, row.attempts) == ("sent", "gmail-1", 1)


def test_opt_out_and_existing_entry_are_skipped_before_sending(calendar_db, factory):
    off = queue(calendar_db, make_user(calendar_db, "off", opt_in=False))
    writer = make_user(calendar_db, "writer")
    calendar_db.add(DayRecord(user_id=writer.user_id, date=TODAY, status="sober"))
    with_entry = queue(calendar_db, writer)
    sender = FakeSender()

    counts = deliver_pending_reminders(factory, EVENING, sender)

    assert counts["skipped"] == 2 and sender.sent == []
    assert (
        status(factory, off).status == status(factory, with_entry).status == "skipped"
    )


def test_rejection_is_retried_in_later_runs_at_most_three_times(calendar_db, factory):
    delivery_id = queue(calendar_db, make_user(calendar_db, "retry"))
    sender = FakeSender([SendRejected("GMAIL_HTTP_500")] * 4)

    results = [deliver_pending_reminders(factory, EVENING, sender) for _ in range(4)]

    assert [r["failed"] for r in results] == [1, 1, 1, 0]
    row = status(factory, delivery_id)
    assert (row.status, row.attempts, row.last_error_code) == (
        "failed",
        3,
        "GMAIL_HTTP_500",
    )


@pytest.mark.parametrize(
    "error", [SendUncertain("GMAIL_NETWORK"), RuntimeError("crash")]
)
def test_uncertain_result_becomes_unknown_without_retry(calendar_db, factory, error):
    delivery_id = queue(calendar_db, make_user(calendar_db, "unsure"))
    sender = FakeSender([error])

    first = deliver_pending_reminders(factory, EVENING, sender)
    again = deliver_pending_reminders(factory, EVENING, sender)

    assert first["unknown"] == 1 and again["unknown"] == 0
    assert len(sender.sent) == 1
    assert status(factory, delivery_id).status == "unknown"


def test_stale_sending_becomes_unknown_and_past_dates_are_skipped(calendar_db, factory):
    stale = queue(
        calendar_db,
        make_user(calendar_db, "stale"),
        status="sending",
        attempts=1,
        claimed_at=EVENING - dt.timedelta(minutes=6),
    )
    old = queue(
        calendar_db, make_user(calendar_db, "old"), TODAY - dt.timedelta(days=1)
    )
    sender = FakeSender()

    deliver_pending_reminders(factory, EVENING, sender)

    assert status(factory, stale).status == "unknown"
    assert status(factory, old).status == "skipped"
    assert sender.sent == []


def test_nothing_is_sent_after_kyiv_midnight(calendar_db, factory):
    delivery_id = queue(calendar_db, make_user(calendar_db, "late"))
    sender = FakeSender()
    after_midnight = dt.datetime(2026, 10, 31, 0, 1, tzinfo=BUSINESS_TIMEZONE)

    deliver_pending_reminders(factory, EVENING, sender, clock=lambda: after_midnight)

    assert sender.sent == []
    assert status(factory, delivery_id).status == "pending"


def test_message_has_neutral_subject_and_shared_reply_to():
    message = build_message(
        "rehab.support.web@gmail.com", "a@example.test", SUBJECT, "текст"
    )

    assert message["Subject"] == "Нагадування Rehab"
    assert message["Reply-To"] == message["From"] == "rehab.support.web@gmail.com"
    assert message["To"] == "a@example.test"


def test_calendar_link_uses_public_frontend(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS", "http://localhost:8081, https://rehab-web.example/"
    )

    assert email_reminders.calendar_url() == "https://rehab-web.example/calendar"


@pytest.fixture
def job_client(engine, monkeypatch):
    monkeypatch.setenv("REMINDERS_JOB_TOKEN", TOKEN)
    calls = []

    def creator(db, now):
        calls.append(now)
        return {"created_in_app": 2, "queued_email": 1, "skipped": 3}

    app = FastAPI()
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(jobs.router)
    sender = FakeSender()
    app.dependency_overrides[jobs.get_engine_for_job] = lambda: engine
    app.dependency_overrides[jobs.get_reminder_creator] = lambda: creator
    app.dependency_overrides[jobs.get_sender] = lambda: sender
    app.dependency_overrides[jobs.get_clock] = lambda: (lambda: EVENING)
    client = TestClient(app)
    client.calls, client.sender = calls, sender
    return client


@pytest.mark.parametrize("headers", [{}, {"X-Job-Token": "wrong"}])
def test_job_rejects_missing_or_wrong_token(job_client, headers):
    response = job_client.post("/internal/jobs/reminders", headers=headers)

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_JOB_TOKEN"
    assert job_client.calls == []


def test_job_is_not_configured_without_strong_secret(job_client, monkeypatch):
    monkeypatch.setenv("REMINDERS_JOB_TOKEN", "short")

    response = job_client.post(
        "/internal/jobs/reminders", headers={"X-Job-Token": "short"}
    )

    assert response.status_code == 503
    assert job_client.calls == []


def test_job_has_no_get_trigger(job_client):
    response = job_client.get(
        "/internal/jobs/reminders", headers={"X-Job-Token": TOKEN}
    )

    assert response.status_code == 405


def test_job_creates_and_delivers_and_returns_only_counters(job_client, calendar_db):
    queue(calendar_db, make_user(calendar_db, "mail"))

    response = job_client.post(
        "/internal/jobs/reminders", headers={"X-Job-Token": TOKEN}
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "created_in_app": 2,
        "queued_email": 1,
        "sent": 1,
        "skipped": 3,
        "failed": 0,
        "unknown": 0,
    }
    assert job_client.calls == [EVENING]
    assert "mail@example.test" not in response.text


def test_parallel_job_is_rejected_while_lock_is_held(job_client, engine):
    with jobs.job_lock(engine) as held:
        assert held
        response = job_client.post(
            "/internal/jobs/reminders", headers={"X-Job-Token": TOKEN}
        )

    assert response.status_code == 409
    assert response.json()["code"] == "JOB_ALREADY_RUNNING"
    assert job_client.calls == []


def test_two_concurrent_workers_send_each_delivery_once(calendar_db, factory):
    for name in ("p1", "p2", "p3", "p4"):
        queue(calendar_db, make_user(calendar_db, name))
    sender = FakeSender()
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()
        deliver_pending_reminders(factory, EVENING, sender)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(to for to, _, _ in sender.sent) == [
        f"p{i}@example.test" for i in range(1, 5)
    ]
    with factory() as db:
        assert set(db.scalars(select(EmailReminderDelivery.status))) == {"sent"}


# AI-GENERATED END
