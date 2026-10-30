import datetime as dt
import pytest
from backend.app.services.reminder_rules import reminder_date, eligible_for_reminder


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        ("2026-03-28T17:59:00+00:00", None),
        ("2026-03-28T18:00:00+00:00", "2026-03-28"),
        ("2026-03-29T16:59:00+00:00", None),
        ("2026-03-29T17:00:00+00:00", "2026-03-29"),
        ("2026-10-24T17:00:00+00:00", "2026-10-24"),
        ("2026-10-25T17:59:00+00:00", None),
        ("2026-10-25T18:00:00+00:00", "2026-10-25"),
        ("2026-10-25T22:00:00+00:00", None),
    ],
)
def test_kyiv_20_hour_boundary_and_both_dst_changes(instant, expected):
    result = reminder_date(dt.datetime.fromisoformat(instant))
    assert (result.isoformat() if result else None) == expected


def test_naive_datetime_is_rejected():
    with pytest.raises(ValueError):
        reminder_date(dt.datetime(2026, 10, 30, 20))


@pytest.mark.parametrize(
    ("role", "start", "explicit", "expected"),
    [
        ("user", "2026-10-29", False, True),
        ("mentor", "2026-10-30", False, True),
        ("admin", "2026-10-29", False, False),
        ("user", "2026-10-31", False, False),
        ("user", "2026-10-29", True, False),
    ],
)
def test_only_tracking_non_admin_accounts_without_explicit_record(
    role, start, explicit, expected
):
    assert (
        eligible_for_reminder(
            role=role,
            tracking_start_date=dt.date.fromisoformat(start),
            business_date=dt.date(2026, 10, 30),
            has_explicit_entry=explicit,
        )
        is expected
    )
