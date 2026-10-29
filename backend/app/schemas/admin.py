# AI-GENERATED START
"""Схеми адмінського API: акаунти й анонімна діаграма тригерів."""

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models import TriggerCategory


class AdminUserOut(BaseModel):
    """Публічний стан акаунта. Без password_hash і token_version."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    nickname: str
    email: str
    role: Literal["user", "mentor", "admin"]
    is_blocked: bool


class AdminUserList(BaseModel):
    items: list[AdminUserOut]
    total: int
    limit: int
    offset: int


class BlockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_blocked: bool = Field(..., description="true: заблокувати, false: розблокувати.")


class TriggerStat(BaseModel):
    category: TriggerCategory
    count: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)


class TriggerDistributionOut(BaseModel):
    """Розбивка зривів за категоріями без ідентифікаторів, імен і email."""

    period_start: dt.date
    period_end: dt.date
    total: int = Field(..., ge=0, description="Зриви із вказаною категорією.")
    categories: list[TriggerStat]


# AI-GENERATED END
