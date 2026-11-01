from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Identity,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.core.mentor_codes import generate_mentor_code


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "mentor_code ~ '^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{12}$'",
            name="mentor_code_format",
        ),
        CheckConstraint(
            "message_style IN ('formal','humorous','zen','strict')",
            name="message_style",
        ),
    )

    user_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    email: Mapped[str] = mapped_column(
        String(254), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    mentor_code: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        unique=True,
        default=generate_mentor_code,
        server_default=text("rehab_new_mentor_code()"),
    )
    email_reminders_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    message_style: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        default="formal",
        server_default="formal",
    )
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(12), nullable=False, default="user")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tracking_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
