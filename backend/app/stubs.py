"""Дані-заглушки в пам'яті замість PostgreSQL (ADR-002).

Стартові дані (для користувача з id=42):
  - початок відстеження: 6 днів тому
  - запис №1: створений 5 днів тому, редагувати вже не можна (FR-008 -> 403)
  - запис №2: створений годину тому, редагувати можна
"""

import datetime as dt
from itertools import count

from backend.app.models import DayStatus, EntryOut, TriggerCategory

entries: dict[int, EntryOut] = {}
tracking_start_dates: dict[int, dt.date] = {}

_entry_ids = count(1)


def next_entry_id() -> int:
    return next(_entry_ids)


def reset() -> None:
    """Скидає сховище до стартових даних (використовується в тестах)."""

    global _entry_ids

    entries.clear()
    tracking_start_dates.clear()

    _entry_ids = count(1)

    now = dt.datetime.now(dt.timezone.utc)
    today = dt.date.today()

    tracking_start_dates[42] = today - dt.timedelta(days=6)

    for rec in (
        EntryOut(
            record_id=next_entry_id(),
            user_id=42,
            date=today - dt.timedelta(days=5),
            status=DayStatus.sober,
            trigger_category=None,
            created_at=now - dt.timedelta(days=5),
        ),
        EntryOut(
            record_id=next_entry_id(),
            user_id=42,
            date=today - dt.timedelta(days=1),
            status=DayStatus.relapse,
            trigger_category=TriggerCategory.stress,
            created_at=now - dt.timedelta(hours=1),
        ),
    ):
        entries[rec.record_id] = rec

reset()
