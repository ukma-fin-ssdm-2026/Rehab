"""Pydantic-схеми API.

Поля відповідають ER-моделі (docs/architecture/data-model.md):
DayRecord -> Entry*, Goal -> Goal*. Додатково описано єдиний формат помилки.
"""

import datetime as dt
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ---------- Перелічення ----------

class DayStatus(str, Enum):
    """Статус дня в календарі (DayRecord.status)."""

    sober = "sober"
    relapse = "relapse"


class TriggerCategory(str, Enum):
    """Категорія тригера зриву (DayRecord.trigger_category)."""

    stress = "stress"
    holiday = "holiday"
    social = "social"
    other = "other"


# ---------- Календар (DayRecord) ----------

class EntryBase(BaseModel):
    """Базові поля відмітки дня."""

    status: DayStatus = Field(
        ...,
        description="Статус дня: `sober` (тверезий) або `relapse` (зрив).",
        examples=["sober"],
    )

    trigger_category: TriggerCategory | None = Field(
        None,
        description="Категорія тригера. Дозволена лише для `status=relapse`.",
    )

    @model_validator(mode="after")
    def trigger_only_for_relapse(self):
        """Забороняє вказувати тригер для тверезого дня."""

        if (
            self.trigger_category is not None
            and self.status != DayStatus.relapse
        ):
            raise ValueError(
                "trigger_category можна вказувати лише для status=relapse"
            )

        return self


class EntryCreate(EntryBase):
    """Тіло запиту на створення відмітки дня (FR-001, FR-002)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "sober",
                    "trigger_category": None,
                    "date": "2026-10-07",
                },
                {
                    "status": "relapse",
                    "trigger_category": "stress",
                    "date": "2026-10-07",
                },
            ]
        }
    )

    date: dt.date = Field(
        ...,
        description=(
            "Дата відмітки у форматі YYYY-MM-DD. "
            "Не може бути в майбутньому (FR-002)."
        ),
        examples=["2026-10-07"],
    )

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, value: dt.date) -> dt.date:
        """Забороняє створення відмітки на майбутню дату."""

        if value > dt.date.today():
            raise ValueError(
                "Не можна відмічати майбутні дні (FR-002)"
            )

        return value


class EntryUpdate(EntryBase):
    """Тіло запиту на зміну статусу дня (FR-008).

    Дату змінити не можна.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "sober",
                    "trigger_category": None,
                },
                {
                    "status": "relapse",
                    "trigger_category": "stress",
                },
            ]
        }
    )


class EntryOut(BaseModel):
    """Відмітка дня у відповіді API."""

    record_id: int = Field(
        ...,
        description="Ідентифікатор запису.",
        examples=[1],
    )

    user_id: int = Field(
        ...,
        description="Власник запису.",
        examples=[42],
    )

    date: dt.date = Field(
        ...,
        description="Дата відмітки.",
        examples=["2026-10-07"],
    )

    status: DayStatus = Field(
        ...,
        description="Статус дня.",
    )

    trigger_category: TriggerCategory | None = Field(
        None,
        description="Категорія тригера зриву.",
    )

    created_at: dt.datetime = Field(
        ...,
        description=(
            "Час створення запису (UTC). "
            "Від нього рахується вікно редагування 48 год (FR-008)."
        ),
    )


class EntryList(BaseModel):
    """Сторінка зі списком відміток."""

    items: list[EntryOut] = Field(
        ...,
        description="Записи поточної сторінки.",
    )

    total: int = Field(
        ...,
        description="Загальна кількість записів за фільтром.",
        examples=[120],
    )

    limit: int = Field(
        ...,
        description="Розмір сторінки.",
        examples=[30],
    )

    offset: int = Field(
        ...,
        description="Зміщення від початку.",
        examples=[0],
    )


# ---------- Цілі (Goal) ----------

class GoalCreate(BaseModel):
    """Тіло запиту на створення або повну заміну цілі (FR-004)."""

    target_days: int = Field(
        ...,
        ge=1,
        le=3650,
        description=(
            "Цільова кількість днів без алкоголю "
            "(від 1 до 3650)."
        ),
        examples=[30],
    )


class GoalOut(BaseModel):
    """Ціль у відповіді API."""

    goal_id: int = Field(
        ...,
        description="Ідентифікатор цілі.",
        examples=[1],
    )

    user_id: int = Field(
        ...,
        description="Власник цілі.",
        examples=[42],
    )

    target_days: int = Field(
        ...,
        description="Цільова кількість днів.",
        examples=[30],
    )

    is_achieved: bool = Field(
        ...,
        description=(
            "Чи досягнуто ціль. Виставляє система, "
            "коли серія доходить до цілі (FR-005)."
        ),
    )


# ---------- Помилки ----------

class ErrorResponse(BaseModel):
    """Єдиний формат помилки для всіх ендпоінтів."""

    code: str = Field(
        ...,
        description="Машинозчитуваний код помилки.",
        examples=["FUTURE_DATE_NOT_ALLOWED"],
    )

    message: str = Field(
        ...,
        description="Пояснення для людини.",
        examples=["Не можна відмічати майбутні дні"],
    )

    details: dict | list | None = Field(
        None,
        description=(
            "Додаткові подробиці "
            "(наприклад, перелік полів з помилками)."
        ),
    )