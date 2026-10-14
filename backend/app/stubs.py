"""Дані-заглушки в пам'яті замість PostgreSQL (ADR-002).

Стартові дані (для користувача з id=42):
  - запис №1: створений 5 днів тому, редагувати вже не можна (FR-008 -> 403)
  - запис №2: створений годину тому, редагувати можна
  - ціль №1: 30 днів
"""

import datetime as dt
from itertools import count

from backend.app.models import DayStatus, EntryOut, GoalOut, TriggerCategory

entries: dict[int, EntryOut] = {}
goals: dict[int, GoalOut] = {}
_entry_ids = count(1)
_goal_ids = count(1)


def next_entry_id() -> int:
    return next(_entry_ids)


def next_goal_id() -> int:
    return next(_goal_ids)


def reset() -> None:
    """Скидає сховище до стартових даних (використовується в тестах)."""
    global _entry_ids, _goal_ids
    entries.clear()
    goals.clear()
    _entry_ids = count(1)
    _goal_ids = count(1)

    now = dt.datetime.now(dt.timezone.utc)
    today = dt.date.today()

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

    goal = GoalOut(
        goal_id=next_goal_id(), user_id=42, target_days=30, is_achieved=False
    )
    goals[goal.goal_id] = goal


reset()
