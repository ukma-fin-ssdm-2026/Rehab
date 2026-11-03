"""A directed relationship remains in history after access is revoked."""

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Mentorship(Base):
    __tablename__ = "mentorships"
    __table_args__ = (
        UniqueConstraint("mentor_id", "mentee_id", name="uq_mentorships_pair"),
        CheckConstraint("mentor_id <> mentee_id", name="different_users"),
        CheckConstraint("status IN ('active','ended')", name="status"),
        CheckConstraint(
            "(status='active' AND ended_at IS NULL AND ended_by IS NULL AND ended_reason IS NULL) OR "
            "(status='ended' AND ended_at IS NOT NULL AND ended_by IS NOT NULL AND ended_reason IS NOT NULL AND "
            "ended_reason IN ('mentor_left','mentee_left','complaint'))",
            name="ending",
        ),
        Index(
            "uq_mentorships_active_mentee",
            "mentee_id",
            unique=True,
            postgresql_where=text("status='active'"),
        ),
        Index("ix_mentorships_mentor_status", "mentor_id", "status"),
    )
    relationship_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    mentee_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    ended_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    ended_reason: Mapped[str | None] = mapped_column(String(16))
