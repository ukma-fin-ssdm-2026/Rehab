# AI-GENERATED START
"""Схеми адмінського API: анонімна діаграма тригерів."""

import datetime as dt
from pydantic import BaseModel, Field

from backend.app.models import TriggerCategory


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
