"""One immutable support comment per relapse notification."""

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class SupportComment(Base):
    __tablename__ = "support_comments"
    __table_args__ = (
        CheckConstraint("length(btrim(text)) BETWEEN 1 AND 2000", name="text"),
    )
    support_comment_id: Mapped[int] = mapped_column(
        Integer, Identity(), primary_key=True
    )
    relationship_id: Mapped[int] = mapped_column(
        ForeignKey("mentorships.relationship_id"), nullable=False
    )
    relapse_notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.notification_id"), nullable=False, unique=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
