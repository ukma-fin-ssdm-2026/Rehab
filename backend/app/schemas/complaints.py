# AI-GENERATED START
"""Схеми скарг підопічного на ментора та адмінського розгляду."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ComplaintStatus = Literal["pending", "approved", "rejected"]


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_id: int = Field(..., ge=1)
    reason: str = Field(..., min_length=1, max_length=2000)
    support_comment_id: int | None = Field(None, ge=1)

    @field_validator("reason", mode="before")
    @classmethod
    def strip_reason(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: int
    relationship_id: int
    reason: str
    support_comment_id: int | None
    status: ComplaintStatus
    created_at: datetime
    reviewed_at: datetime | None


class ComplaintParty(BaseModel):
    """Тільки фігуранти скарги: без ролі, коду, налаштувань чи фото."""

    model_config = ConfigDict(from_attributes=True)

    nickname: str
    email: str


class ComplaintEvidence(BaseModel):
    text: str
    created_at: datetime | None


class AdminComplaintOut(ComplaintOut):
    reporter: ComplaintParty
    reported: ComplaintParty
    evidence: ComplaintEvidence | None


class AdminComplaintList(BaseModel):
    items: list[AdminComplaintOut]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


class ComplaintDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approved", "rejected"]


class AdminOverview(BaseModel):
    registrations_last_30_days: int = Field(..., ge=0)
    active_mentors: int = Field(..., ge=0)
    active_relationships: int = Field(..., ge=0)
    pending_complaints: int = Field(..., ge=0)
    current_date: date


# AI-GENERATED END
