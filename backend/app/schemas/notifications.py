"""DTO contract for notifications; persistence is integrated after KT-A."""

from datetime import date
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class ContactOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nickname: str
    email: str


class SupportCommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=2000, strict=True)

    @field_validator("text", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class SupportCommentOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    support_comment_id: int = Field(gt=0)
    relationship_id: int = Field(gt=0)
    relapse_notification_id: int = Field(gt=0)
    author: ContactOut
    text: str
    created_at: AwareDatetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notification_id: int = Field(gt=0)
    kind: Literal["daily_reminder", "relapse", "support_comment"]
    created_at: AwareDatetime
    read_at: AwareDatetime | None
    business_date: date
    relationship_id: int | None
    record_id: int | None
    sender: ContactOut | None
    title: str
    body: str
    support_comment: SupportCommentOut | None
    can_support: bool
    can_view_mentee: bool
    can_report_mentor: bool


class NotificationList(BaseModel):
    items: list[NotificationOut]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class UnreadCount(BaseModel):
    count: int = Field(ge=0)
