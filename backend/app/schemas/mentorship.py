"""Agreed DTOs for the next mentorship API/UI implementation stage."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MentorshipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(pattern=r"^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{12}$")

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value


class RelationshipContact(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    nickname: str
    email: str


class RelationshipOut(BaseModel):
    relationship_id: int
    status: Literal["active", "ended"]
    mentor: RelationshipContact
    mentee: RelationshipContact
    created_at: datetime
    ended_at: datetime | None
    ended_reason: Literal["mentor_left", "mentee_left", "complaint"] | None


class RelationshipList(BaseModel):
    items: list[RelationshipOut]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
