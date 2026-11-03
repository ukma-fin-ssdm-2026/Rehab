"""Pair-specific moderation, optionally retaining an attached comment."""

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','rejected')", name="status"),
        CheckConstraint("length(btrim(reason)) BETWEEN 1 AND 2000", name="reason"),
        CheckConstraint("reporter_id <> reported_id", name="different_users"),
        CheckConstraint(
            "(status='pending' AND reviewed_at IS NULL AND reviewed_by IS NULL) OR (status IN ('approved','rejected') AND reviewed_at IS NOT NULL AND reviewed_by IS NOT NULL)",
            name="review",
        ),
        Index(
            "uq_complaints_pending_pair",
            "reporter_id",
            "reported_id",
            unique=True,
            postgresql_where=text("status='pending'"),
        ),
        Index("ix_complaints_status_created", "status", "created_at"),
    )
    complaint_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    relationship_id: Mapped[int] = mapped_column(
        ForeignKey("mentorships.relationship_id"), nullable=False
    )
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )
    reported_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    support_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("support_comments.support_comment_id")
    )
    evidence_text: Mapped[str | None] = mapped_column(String(2000))
    evidence_created_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pending", server_default="pending"
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
