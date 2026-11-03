import datetime as dt
from sqlalchemy import select, func
from backend.app.db.models.user import User
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.notification import Notification
from backend.app.db.models.email_delivery import EmailReminderDelivery
from backend.app.services.reminders import create_due_reminders


def test_due_reminders_are_current_day_opt_in_and_idempotent(calendar_db, db_users):
    db = calendar_db
    now = dt.datetime(2026, 10, 31, 18, tzinfo=dt.timezone.utc)
    for user_id in db_users:
        account = db.get(User, user_id)
        account.tracking_start_date = dt.date(2026, 10, 1)
    db.get(User, db_users[0]).email_reminders_enabled = True
    db.commit()
    assert create_due_reminders(db, now - dt.timedelta(minutes=1)) == {
        "created_in_app": 0,
        "queued_email": 0,
        "skipped": 0,
    }
    result = create_due_reminders(db, now)
    db.commit()
    assert result == {"created_in_app": 2, "queued_email": 1, "skipped": 0}
    assert create_due_reminders(db, now)["created_in_app"] == 0
    db.commit()
    assert db.scalar(select(func.count()).select_from(Notification)) == 2
    assert db.scalar(select(func.count()).select_from(EmailReminderDelivery)) == 1
    assert set(db.scalars(select(Notification.business_date))) == {
        dt.date(2026, 10, 31)
    }


def test_explicit_sober_and_admin_are_excluded(calendar_db, db_users):
    db = calendar_db
    now = dt.datetime(2026, 10, 31, 18, tzinfo=dt.timezone.utc)
    for user_id in db_users:
        db.get(User, user_id).tracking_start_date = dt.date(2026, 10, 1)
    db.add(DayRecord(user_id=db_users[0], date=now.date(), status="sober", drinks=[]))
    db.get(User, db_users[1]).role = "admin"
    db.commit()
    result = create_due_reminders(db, now)
    db.commit()
    assert result["created_in_app"] == result["queued_email"] == 0


def test_reminder_and_email_task_roll_back_together(calendar_db, db_users):
    db = calendar_db
    for user_id in db_users:
        db.get(User, user_id).tracking_start_date = dt.date(2026, 10, 1)
        db.get(User, user_id).email_reminders_enabled = True
    db.commit()
    now = dt.datetime(2026, 10, 31, 18, tzinfo=dt.timezone.utc)
    assert create_due_reminders(db, now)["queued_email"] == 2
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Notification)) == 0
    assert db.scalar(select(func.count()).select_from(EmailReminderDelivery)) == 0
    assert create_due_reminders(db, now)["created_in_app"] == 2


def test_parallel_jobs_do_not_duplicate_inbox_or_email(
    calendar_db, db_users, postgres_schema
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session

    db = calendar_db
    for user_id in db_users:
        user = db.get(User, user_id)
        user.tracking_start_date = dt.date(2026, 10, 1)
        user.email_reminders_enabled = True
    db.commit()
    barrier = Barrier(2)

    def run():
        with Session(postgres_schema) as session:
            barrier.wait(timeout=10)
            result = create_due_reminders(
                session, dt.datetime(2026, 10, 31, 18, tzinfo=dt.timezone.utc)
            )
            session.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(run) for _ in range(2)]
        results = [job.result(timeout=20) for job in jobs]
    assert sum(result["created_in_app"] for result in results) == 2
    assert sum(result["queued_email"] for result in results) == 2
    assert db.scalar(select(func.count()).select_from(Notification)) == 2
    assert db.scalar(select(func.count()).select_from(EmailReminderDelivery)) == 2


def test_more_than_one_batch_is_processed_with_bounded_selects(
    calendar_db, postgres_schema
):
    from sqlalchemy import event

    db = calendar_db
    db.add_all(
        [
            User(
                email=f"batch-{index}@example.test",
                name="Batch",
                nickname=f"batch-{index}",
                password_hash="test-only",
                tracking_start_date=dt.date(2026, 10, 1),
            )
            for index in range(101)
        ]
    )
    db.commit()
    selections = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        if "SELECT users.user_id \n" in statement:
            selections.append(statement)

    event.listen(postgres_schema, "before_cursor_execute", capture)
    try:
        result = create_due_reminders(
            db, dt.datetime(2026, 10, 31, 18, tzinfo=dt.timezone.utc)
        )
        db.commit()
    finally:
        event.remove(postgres_schema, "before_cursor_execute", capture)
    assert result["created_in_app"] == 101
    assert len(selections) >= 2
    assert all("LIMIT" in query for query in selections)
