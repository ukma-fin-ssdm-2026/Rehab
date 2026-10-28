import datetime as dt

import pytest

from backend.app.models import DayStatus, EntryOut, TriggerCategory
from backend.app.services.statistics import calculate_trigger_distribution


def make_entry(
    *,
    day: dt.date,
    status: DayStatus = DayStatus.relapse,
    category: TriggerCategory | None = None,
    user_id: int = 42,
) -> EntryOut:
    return EntryOut(
        record_id=1,
        user_id=user_id,
        date=day,
        status=status,
        trigger_category=category,
        created_at=dt.datetime(2026, 10, 28, tzinfo=dt.timezone.utc),
    )


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        pytest.param(
            [
                make_entry(day=dt.date(2026, 10, 28), category=TriggerCategory.stress),
                make_entry(day=dt.date(2026, 10, 27), category=TriggerCategory.stress),
                make_entry(day=dt.date(2026, 10, 26), category=TriggerCategory.social),
                make_entry(day=dt.date(2026, 10, 25), category=TriggerCategory.holiday),
            ],
            {"stress": 50.0, "holiday": 25.0, "social": 25.0, "other": 0.0},
            id="percentages-include-all-categories",
        ),
        pytest.param(
            [
                make_entry(day=dt.date(2026, 9, 29), category=TriggerCategory.stress),
                make_entry(day=dt.date(2026, 10, 29), category=TriggerCategory.social),
                make_entry(day=dt.date(2026, 10, 28), status=DayStatus.sober),
                make_entry(day=dt.date(2026, 10, 28), category=None),
            ],
            {"stress": 0.0, "holiday": 0.0, "social": 0.0, "other": 0.0},
            id="exclude-outside-window-sober-and-uncategorized",
        ),
    ],
)
def test_trigger_distribution_uses_only_anonymous_categorized_relapses_in_last_30_days(
    entries: list[EntryOut], expected: dict[str, float]
) -> None:
    result = calculate_trigger_distribution(entries, today=dt.date(2026, 10, 28))

    assert result["period_start"] == dt.date(2026, 9, 29)
    assert result["period_end"] == dt.date(2026, 10, 28)
    assert result["total"] == sum(item["count"] for item in result["categories"])
    assert {
        item["category"]: item["percentage"] for item in result["categories"]
    } == expected
    assert all("user_id" not in item for item in result["categories"])


def test_trigger_distribution_rejects_future_reference_date() -> None:
    with pytest.raises(ValueError, match="Дата звіту не може бути в майбутньому"):
        calculate_trigger_distribution([], today=dt.date(2026, 10, 29))

