"""Transactional notifications and support. No helper commits or rolls back."""

from sqlalchemy import select, update
from backend.app.core.clock import utc_now
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.notification import Notification
from backend.app.db.models.support_comment import SupportComment
from backend.app.db.models.user import User
from backend.app.errors import api_error
from backend.app.repositories.notifications import own_notification, insert_once
from backend.app.schemas.notifications import (
    ContactOut,
    NotificationOut,
    SupportCommentOut,
)
from backend.app.services.mentorship import require_active_mentor
from backend.app.services.message_texts import render_message


def emit_relapse_once(db, record_id: int, previous_status: str | None) -> None:
    """Calendar caller holds mentee user -> mentorship -> record locks before flush.

    Do not acquire earlier locks here: that would reverse the caller's order.
    The conditional marker is written even when no active mentor exists.
    """
    if previous_status not in (None, "sober"):
        return
    row = db.execute(
        update(DayRecord)
        .where(
            DayRecord.record_id == record_id,
            DayRecord.status == "relapse",
            DayRecord.first_relapse_at.is_(None),
        )
        .values(first_relapse_at=utc_now())
        .returning(DayRecord.user_id, DayRecord.date)
    ).first()
    if row is None:
        return
    relationship = db.scalar(
        select(Mentorship).where(
            Mentorship.mentee_id == row.user_id, Mentorship.status == "active"
        )
    )
    if relationship is None:
        return
    insert_once(
        db,
        recipient_id=relationship.mentor_id,
        sender_id=row.user_id,
        kind="relapse",
        event_key=f"relapse:{row.user_id}:{row.date.isoformat()}",
        business_date=row.date,
        relationship_id=relationship.relationship_id,
        record_id=record_id,
    )


def _contact(db, user_id):
    person = db.get(User, user_id) if user_id is not None else None
    return ContactOut(nickname=person.nickname, email=person.email) if person else None


def comment_out(db, comment):
    return SupportCommentOut(
        support_comment_id=comment.support_comment_id,
        relationship_id=comment.relationship_id,
        relapse_notification_id=comment.relapse_notification_id,
        author=_contact(db, comment.author_id),
        text=comment.text,
        created_at=comment.created_at,
    )


def notification_out(db, item, variation: int = 0):
    receiver = db.get(User, item.recipient_id)
    relationship = (
        db.scalar(
            select(Mentorship)
            .where(Mentorship.relationship_id == item.relationship_id)
            .execution_options(populate_existing=True)
        )
        if item.relationship_id
        else None
    )
    record = (
        db.scalar(
            select(DayRecord)
            .where(DayRecord.record_id == item.record_id)
            .execution_options(populate_existing=True)
        )
        if item.record_id
        else None
    )
    comment = (
        db.get(SupportComment, item.support_comment_id)
        if item.support_comment_id
        else None
    )
    if item.kind == "relapse" and comment is None:
        comment = db.scalar(
            select(SupportComment).where(
                SupportComment.relapse_notification_id == item.notification_id
            )
        )
    active_mentor = bool(
        relationship
        and relationship.status == "active"
        and relationship.mentor_id == item.recipient_id
    )
    can_view = item.kind == "relapse" and active_mentor
    can_support = bool(
        can_view and record and record.status == "relapse" and comment is None
    )
    can_report = bool(
        item.kind == "support_comment"
        and comment
        and relationship
        and relationship.mentee_id == item.recipient_id
        and comment.recipient_id == item.recipient_id
        and comment.author_id == relationship.mentor_id
    )
    sender = _contact(db, item.sender_id)
    key = (
        "relapse.corrected"
        if item.kind == "relapse" and record and record.status != "relapse"
        else item.kind
    )
    title, body = render_message(
        key,
        receiver.message_style,
        {
            "nickname": sender.nickname if sender else "",
            "date": item.business_date.isoformat(),
        },
        variation=variation,
    )
    return NotificationOut(
        notification_id=item.notification_id,
        kind=item.kind,
        created_at=item.created_at,
        read_at=item.read_at,
        business_date=item.business_date,
        relationship_id=item.relationship_id,
        record_id=item.record_id,
        sender=sender,
        title=title,
        body=body,
        support_comment=comment_out(db, comment) if comment else None,
        can_support=can_support,
        can_view_mentee=can_view,
        can_report_mentor=can_report,
    )


def send_support(db, actor_id: int, notification_id: int, text: str):
    source = own_notification(db, actor_id, notification_id)
    if source.kind != "relapse" or source.relationship_id is None:
        raise api_error(404, "NOTIFICATION_NOT_FOUND", "Повідомлення не знайдено")
    relationship = require_active_mentor(
        db, actor_id, source.relationship_id, lock=True
    )
    record = db.scalar(
        select(DayRecord)
        .where(
            DayRecord.record_id == source.record_id,
            DayRecord.user_id == relationship.mentee_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    source = own_notification(db, actor_id, notification_id, lock=True)
    if (
        db.scalar(
            select(SupportComment.support_comment_id).where(
                SupportComment.relapse_notification_id == notification_id
            )
        )
        is not None
    ):
        raise api_error(409, "SUPPORT_ALREADY_SENT", "Підтримку вже надіслано")
    if record is None or record.status != "relapse":
        raise api_error(
            409, "RELAPSE_NO_LONGER_ACTIVE", "Запис уже не позначено як зрив"
        )
    comment = SupportComment(
        relationship_id=relationship.relationship_id,
        relapse_notification_id=source.notification_id,
        author_id=actor_id,
        recipient_id=relationship.mentee_id,
        text=text,
    )
    db.add(comment)
    db.flush()
    source.support_comment_id = comment.support_comment_id
    db.add(
        Notification(
            recipient_id=relationship.mentee_id,
            sender_id=actor_id,
            kind="support_comment",
            event_key=f"support:{comment.support_comment_id}",
            business_date=source.business_date,
            relationship_id=relationship.relationship_id,
            record_id=record.record_id,
            support_comment_id=comment.support_comment_id,
        )
    )
    db.flush()
    return comment_out(db, comment)
