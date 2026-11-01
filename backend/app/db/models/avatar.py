"""Small normalized avatars persist independently from auth responses."""

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UserAvatar(Base):
    __tablename__ = "user_avatars"
    __table_args__ = (
        CheckConstraint("mime_type='image/jpeg'", name="mime_type"),
        CheckConstraint(
            "octet_length(image_data) BETWEEN 1 AND 262144", name="image_size"
        ),
        CheckConstraint("version >= 1", name="version"),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    mime_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="image/jpeg", server_default="image/jpeg"
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
