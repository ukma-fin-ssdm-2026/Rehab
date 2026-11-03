"""Recipient-scoped inbox queries; callers own their transaction."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from backend.app.db.models.notification import Notification
from backend.app.errors import api_error


def own_notification(db, recipient_id, notification_id, *, lock=False):
    query = select(Notification).where(
        Notification.notification_id == notification_id,
        Notification.recipient_id == recipient_id,
    )
    if lock:
        query = query.with_for_update()
    item = db.scalar(query.execution_options(populate_existing=True))
    if item is None:
        raise api_error(404, "NOTIFICATION_NOT_FOUND", "Повідомлення не знайдено")
    return item


def list_notifications(db, recipient_id, limit, offset):
    query = select(Notification).where(Notification.recipient_id == recipient_id)
    return list(
        db.scalars(
            query.order_by(
                Notification.created_at.desc(), Notification.notification_id.desc()
            )
            .limit(limit)
            .offset(offset)
        )
    )


def count_notifications(db, recipient_id, *, unread=False):
    query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.recipient_id == recipient_id)
    )
    if unread:
        query = query.where(Notification.read_at.is_(None))
    return db.scalar(query)


def insert_once(db, **values):
    return db.scalar(
        insert(Notification)
        .values(**values)
        .on_conflict_do_nothing(
            index_elements=[Notification.recipient_id, Notification.event_key]
        )
        .returning(Notification.notification_id)
    )
