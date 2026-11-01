"""Pure reminder eligibility; DB creation and delivery integrate after KT-A."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

KYIV = ZoneInfo("Europe/Kyiv")


def reminder_date(now: datetime) -> date | None:
    """Only the current Kyiv day is due, from 20:00 through midnight."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Час нагадування має містити часовий пояс")
    local = now.astimezone(KYIV)
    return local.date() if local.hour >= 20 else None


def eligible_for_reminder(
    *,
    role: str,
    tracking_start_date: date,
    business_date: date,
    has_explicit_entry: bool
) -> bool:
    return (
        role in ("user", "mentor")
        and tracking_start_date <= business_date
        and not has_explicit_entry
    )
