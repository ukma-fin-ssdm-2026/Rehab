"""Persistent opt-in email work; no provider credentials are stored here."""

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
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class EmailReminderDelivery(Base):
    __tablename__ = "email_reminder_deliveries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','sending','sent','skipped','failed','unknown')",
            name="status",
        ),
        CheckConstraint("attempts >= 0", name="attempts"),
        Index("ix_email_reminder_deliveries_status_date", "status", "business_date"),
    )
    delivery_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.notification_id"), nullable=False, unique=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )
    business_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pending", server_default="pending"
    )
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    claimed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    provider_message_id: Mapped[str | None] = mapped_column(String(254))
    last_error_code: Mapped[str | None] = mapped_column(String(100))
