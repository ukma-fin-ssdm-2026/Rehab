"""Create current-day reminders and opt-in outbox work, without sending mail."""

from datetime import datetime
from sqlalchemy import select
from backend.app.db.models.user import User
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.email_delivery import EmailReminderDelivery
from backend.app.repositories.notifications import insert_once
from backend.app.services.reminder_rules import reminder_date, eligible_for_reminder


def create_due_reminders(db, now: datetime) -> dict[str, int]:
    """Caller owns one transaction; recipient locks serialize with calendar writes."""
    counts = {"created_in_app": 0, "queued_email": 0, "skipped": 0}
    day = reminder_date(now)
    if day is None:
        return counts
    cursor = 0
    while True:
        candidates = list(
            db.scalars(
                select(User.user_id)
                .where(
                    User.role.in_(("user", "mentor")),
                    User.tracking_start_date <= day,
                    User.user_id > cursor,
                )
                .order_by(User.user_id)
                .limit(100)
            )
        )
        if not candidates:
            break
        for user_id in candidates:
            person = db.scalar(
                select(User)
                .where(User.user_id == user_id)
                .with_for_update(key_share=True)
                .execution_options(populate_existing=True)
            )
            explicit = (
                db.scalar(
                    select(DayRecord.record_id).where(
                        DayRecord.user_id == user_id, DayRecord.date == day
                    )
                )
                is not None
            )
            if not eligible_for_reminder(
                role=person.role,
                tracking_start_date=person.tracking_start_date,
                business_date=day,
                has_explicit_entry=explicit,
            ):
                counts["skipped"] += 1
                continue
            notification_id = insert_once(
                db,
                recipient_id=user_id,
                kind="daily_reminder",
                event_key=f"reminder:{day.isoformat()}",
                business_date=day,
            )
            if notification_id is None:
                counts["skipped"] += 1
                continue
            counts["created_in_app"] += 1
            if person.email_reminders_enabled:
                db.add(
                    EmailReminderDelivery(
                        notification_id=notification_id,
                        recipient_id=user_id,
                        business_date=day,
                    )
                )
                counts["queued_email"] += 1
        cursor = candidates[-1]
        if len(candidates) < 100:
            break
    db.flush()
    return counts
