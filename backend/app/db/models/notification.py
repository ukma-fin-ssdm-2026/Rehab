"""Private inbox event, deduplicated per recipient and event key."""

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "recipient_id", "event_key", name="uq_notifications_recipient_event"
        ),
        CheckConstraint(
            "kind IN ('daily_reminder','relapse','support_comment')", name="kind"
        ),
        Index(
            "ix_notifications_recipient_created",
            "recipient_id",
            "created_at",
            "notification_id",
        ),
    )
    notification_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    event_key: Mapped[str] = mapped_column(String(100), nullable=False)
    business_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    relationship_id: Mapped[int | None] = mapped_column(
        ForeignKey("mentorships.relationship_id")
    )
    record_id: Mapped[int | None] = mapped_column(ForeignKey("day_records.record_id"))
    support_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "support_comments.support_comment_id",
            name="fk_notifications_support_comment_id_support_comments",
            use_alter=True,
        )
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
