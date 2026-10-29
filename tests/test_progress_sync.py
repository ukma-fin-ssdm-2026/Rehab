import datetime as dt
import sys
import types
from types import SimpleNamespace

import pytest

from backend.app.models import DayStatus, EntryOut
from backend.app.services.progress_sync import recompute_progress


def repository_module(name, **functions):
    module = types.ModuleType(name)
    for function_name, function in functions.items():
        setattr(module, function_name, function)
    return module


def entry(record_id, user_id, entry_date, status):
    return EntryOut(
        record_id=record_id,
        user_id=user_id,
        date=entry_date,
        status=status,
        created_at=dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc),
    )


def install_repositories(monkeypatch, *, user, entries, goals):
    monkeypatch.setitem(
        sys.modules,
        "backend.app.repositories.users",
        repository_module(
            "backend.app.repositories.users",
            get_user=lambda db, user_id: user if user_id == 42 else None,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "backend.app.repositories.entries",
        repository_module(
            "backend.app.repositories.entries",
            list_user_entries=lambda db, user_id: entries,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "backend.app.repositories.goals",
        repository_module(
            "backend.app.repositories.goals",
            list_user_goals=lambda db, user_id: goals,
        ),
    )


def test_recompute_progress_updates_cache_and_achievements(monkeypatch):
    user = SimpleNamespace(
        user_id=42,
        tracking_start_date=dt.date(2026, 10, 1),
        best_streak=10,
    )
    goals = [
        SimpleNamespace(target_days=5, is_achieved=False),
        SimpleNamespace(target_days=6, is_achieved=True),
        SimpleNamespace(target_days=30, is_achieved=False),
    ]
    entries = [
        entry(1, 42, dt.date(2026, 10, 2), DayStatus.relapse),
        entry(2, 42, dt.date(2026, 10, 8), DayStatus.relapse),
        entry(3, 42, dt.date(2026, 10, 11), DayStatus.relapse),
    ]
    install_repositories(monkeypatch, user=user, entries=entries, goals=goals)

    recompute_progress(object(), 42, dt.date(2026, 10, 10))

    assert user.best_streak == 5
    assert [goal.is_achieved for goal in goals] == [True, False, False]


def test_recompute_progress_recalculates_after_history_correction(monkeypatch):
    user = SimpleNamespace(
        user_id=42,
        tracking_start_date=dt.date(2026, 10, 1),
        best_streak=20,
    )
    goals = [
        SimpleNamespace(target_days=7, is_achieved=True),
        SimpleNamespace(target_days=8, is_achieved=True),
    ]
    install_repositories(monkeypatch, user=user, entries=[], goals=goals)

    recompute_progress(object(), 42, dt.date(2026, 10, 7))

    assert user.best_streak == 7
    assert [goal.is_achieved for goal in goals] == [True, False]


def test_recompute_progress_rejects_a_missing_user(monkeypatch):
    install_repositories(monkeypatch, user=None, entries=[], goals=[])

    with pytest.raises(LookupError, match="Користувача 42 не знайдено"):
        recompute_progress(object(), 42, dt.date(2026, 10, 10))


def test_recompute_progress_rejects_a_future_start_date(monkeypatch):
    user = SimpleNamespace(
        user_id=42,
        tracking_start_date=dt.date(2026, 10, 11),
        best_streak=0,
    )
    install_repositories(monkeypatch, user=user, entries=[], goals=[])

    with pytest.raises(ValueError, match="Дата початку відстеження не може бути в майбутньому"):
        recompute_progress(object(), 42, dt.date(2026, 10, 10))
