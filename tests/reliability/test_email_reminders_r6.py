"""R6: перевірки розміру пакета й бюджету часу без PostgreSQL/Gmail."""

import datetime as dt
from types import SimpleNamespace

import pytest

from backend.app.core.clock import BUSINESS_TIMEZONE
from backend.app.services import email_reminders

EVENING = dt.datetime(2026, 10, 30, 20, 15, tzinfo=BUSINESS_TIMEZONE)


class FakeDatabase:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def commit(self):
        pass


class FakeSender:
    def __init__(self, outcomes=None, after_send=None):
        self.outcomes = list(outcomes or [])
        self.after_send = after_send
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append(to)
        if self.after_send:
            self.after_send()
        outcome = self.outcomes.pop(0) if self.outcomes else None
        if isinstance(outcome, Exception):
            raise outcome
        return f"gmail-{len(self.sent)}"


@pytest.fixture
def fake_queue(monkeypatch):
    """Імітація лише черги: не створює БД і не відправляє листів."""
    deliveries = []

    def add(*, wanted=True):
        delivery_id = len(deliveries) + 1
        row = SimpleNamespace(
            delivery_id=delivery_id,
            wanted=wanted,
            status="pending",
            attempts=0,
            last_error_code=None,
        )
        deliveries.append(row)
        return row

    def claim(db, now, today, seen):
        for row in deliveries:
            if row.status in ("pending", "failed") and row.delivery_id not in seen:
                if row.attempts < email_reminders.MAX_ATTEMPTS:
                    row.status = "sending"
                    row.attempts += 1
                    return row
        return None

    def still_wanted(db, row):
        if not row.wanted:
            return None
        return SimpleNamespace(
            email=f"user{row.delivery_id}@example.test", message_style="formal"
        )

    def finish(db_factory, delivery_id, **values):
        row = deliveries[delivery_id - 1]
        for name, value in values.items():
            setattr(row, name, value)

    monkeypatch.setattr(email_reminders, "maintain_reminder_queue", lambda *args: None)
    monkeypatch.setattr(email_reminders, "_claim", claim)
    monkeypatch.setattr(email_reminders, "_still_wanted", still_wanted)
    monkeypatch.setattr(email_reminders, "_finish", finish)
    monkeypatch.setattr(
        email_reminders, "reminder_body", lambda *args: "Тестове нагадування"
    )
    return add, deliveries, FakeDatabase


def test_r6_batch_leaves_rest_for_next_runs(fake_queue):
    add, rows, factory = fake_queue
    for _ in range(7):
        add()
    sender = FakeSender()

    first = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=3
    )
    assert first == {"sent": 3, "skipped": 0, "failed": 0, "unknown": 0}
    assert [row.status for row in rows].count("pending") == 4

    second = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=3
    )
    third = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=3
    )
    fourth = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=3
    )
    assert [result["sent"] for result in (first, second, third, fourth)] == [3, 3, 1, 0]
    assert len(sender.sent) == len(set(sender.sent)) == 7
    assert all(row.status == "sent" and row.attempts == 1 for row in rows)


def test_r6_default_batch_limit_is_bounded(fake_queue):
    add, rows, factory = fake_queue
    for _ in range(27):
        add()
    sender = FakeSender()

    first = email_reminders.deliver_pending_reminders(factory, EVENING, sender)
    assert first["sent"] == 25
    assert [row.status for row in rows].count("pending") == 2


def test_r6_monotonic_budget_stops_between_sends(fake_queue):
    add, rows, factory = fake_queue
    for _ in range(4):
        add()
    tick = [100.0]
    sender = FakeSender(after_send=lambda: tick.__setitem__(0, tick[0] + 6.0))

    first = email_reminders.deliver_pending_reminders(
        factory,
        EVENING,
        sender,
        max_deliveries=10,
        max_duration_seconds=10.0,
        monotonic_clock=lambda: tick[0],
    )
    assert first["sent"] == 2
    assert [row.status for row in rows].count("pending") == 2

    second = email_reminders.deliver_pending_reminders(
        factory,
        EVENING,
        sender,
        max_deliveries=10,
        max_duration_seconds=10.0,
        monotonic_clock=lambda: tick[0],
    )
    assert second["sent"] == 2
    assert all(row.status == "sent" for row in rows)


def test_r6_uncertain_result_not_sent_again(fake_queue):
    add, rows, factory = fake_queue
    add()
    add()
    sender = FakeSender(outcomes=[RuntimeError("розрив з'єднання")])

    first = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=1
    )
    second = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=1
    )
    third = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=1
    )

    assert first["unknown"] == 1
    assert second["sent"] == 1 and third["sent"] == 0
    assert [row.status for row in rows] == ["unknown", "sent"]
    assert len(sender.sent) == 2


def test_r6_in_flight_send_finishes_even_after_budget(fake_queue):
    add, rows, factory = fake_queue
    add()
    add()
    tick = [0.0]
    sender = FakeSender(after_send=lambda: tick.__setitem__(0, 50.0))

    result = email_reminders.deliver_pending_reminders(
        factory,
        EVENING,
        sender,
        max_deliveries=10,
        max_duration_seconds=20.0,
        monotonic_clock=lambda: tick[0],
    )
    assert result["sent"] == 1
    assert [row.status for row in rows] == ["sent", "pending"]


def test_r6_invalid_limits_are_rejected(fake_queue):
    _, _, factory = fake_queue
    with pytest.raises(ValueError, match="Ліміти"):
        email_reminders.deliver_pending_reminders(
            factory, EVENING, FakeSender(), max_deliveries=0
        )
    with pytest.raises(ValueError, match="Ліміти"):
        email_reminders.deliver_pending_reminders(
            factory, EVENING, FakeSender(), max_duration_seconds=0
        )


def test_r6_skips_and_rejections_count_toward_batch(fake_queue):
    add, rows, factory = fake_queue
    add(wanted=False)
    add()
    add()
    sender = FakeSender(outcomes=[email_reminders.SendRejected("GMAIL_HTTP_500")])

    first = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=2
    )
    assert first == {"sent": 0, "skipped": 1, "failed": 1, "unknown": 0}
    assert [row.status for row in rows] == ["skipped", "failed", "pending"]
    assert len(sender.sent) == 1

    second = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, max_deliveries=2
    )
    assert second["sent"] == 2
    assert [row.status for row in rows] == ["skipped", "sent", "sent"]
    assert rows[1].attempts == 2


def test_r6_midnight_still_prevents_late_sends(fake_queue):
    add, rows, factory = fake_queue
    add()
    sender = FakeSender()
    after_midnight = dt.datetime(2026, 10, 31, 0, 1, tzinfo=BUSINESS_TIMEZONE)

    result = email_reminders.deliver_pending_reminders(
        factory, EVENING, sender, clock=lambda: after_midnight
    )
    assert result == {"sent": 0, "skipped": 0, "failed": 0, "unknown": 0}
    assert rows[0].status == "pending"
    assert sender.sent == []
