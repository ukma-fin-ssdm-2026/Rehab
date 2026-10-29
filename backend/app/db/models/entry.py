"""Calendar ORM model matching the shared initial PostgreSQL migration.

AI-GENERATED START: prepared with ChatGPT; PostgreSQL persistence tested.
"""

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class DayRecord(Base):
    __tablename__ = "day_records"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_day_records_user_date"),
        CheckConstraint("status IN ('sober','relapse')", name="status"),
        CheckConstraint(
            "trigger_category IS NULL OR "
            "trigger_category IN ('stress','holiday','social','other')",
            name="trigger",
        ),
        CheckConstraint("jsonb_typeof(drinks) = 'array'", name="drinks_array"),
        CheckConstraint(
            "status = 'relapse' OR "
            "(trigger_category IS NULL AND drinks = '[]'::jsonb)",
            name="sober_fields",
        ),
    )

    record_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    trigger_category: Mapped[str | None] = mapped_column(String(16))
    drinks: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    comment: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# AI-GENERATED END
