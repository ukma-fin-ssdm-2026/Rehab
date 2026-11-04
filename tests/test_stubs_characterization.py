import datetime as dt

from backend.app import stubs
from backend.app.models import DayStatus, TriggerCategory


def test_reset_recreates_original_seed_data():
    stubs.reset()
    try:
        today = dt.date.today()
        assert stubs.tracking_start_dates == {42: today - dt.timedelta(days=6)}
        assert list(stubs.entries) == [1, 2]

        older = stubs.entries[1]
        recent = stubs.entries[2]

        assert (
            older.user_id,
            older.date,
            older.status,
            older.trigger_category,
        ) == (42, today - dt.timedelta(days=5), DayStatus.sober, None)
        assert (
            recent.user_id,
            recent.date,
            recent.status,
            recent.trigger_category,
        ) == (
            42,
            today - dt.timedelta(days=1),
            DayStatus.relapse,
            TriggerCategory.stress,
        )
        assert recent.created_at - older.created_at == dt.timedelta(
            days=4, hours=23
        )
        assert older.created_at.utcoffset() == dt.timedelta(0)
        assert recent.created_at.utcoffset() == dt.timedelta(0)
        assert stubs.next_entry_id() == 3
    finally:
        stubs.reset()


def test_reset_preserves_shared_dictionaries_and_restarts_counter():
    stubs.reset()
    try:
        original_entries = stubs.entries
        original_tracking_dates = stubs.tracking_start_dates

        stubs.entries.pop(1)
        stubs.tracking_start_dates[99] = dt.date(2020, 1, 1)
        assert stubs.next_entry_id() == 3

        stubs.reset()

        assert stubs.entries is original_entries
        assert stubs.tracking_start_dates is original_tracking_dates
        assert list(stubs.entries) == [1, 2]
        assert list(stubs.tracking_start_dates) == [42]
        assert stubs.next_entry_id() == 3
    finally:
        stubs.reset()
