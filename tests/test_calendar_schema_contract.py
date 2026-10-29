"""Calendar requests use the shared day and reject server-owned fields."""

import datetime as dt

from pydantic import ValidationError
import pytest

from backend.app.core import clock
from backend.app.models import EntryCreate


@pytest.mark.parametrize(
    "field,value", [("user_id", 99), ("created_at", "2026-01-01"), ("record_id", 1)]
)
def test_create_rejects_server_owned_fields(field, value):
    with pytest.raises(ValidationError):
        EntryCreate.model_validate(
            {"date": clock.today_local(), "status": "sober", field: value}
        )


def test_comment_has_real_length_limit():
    assert EntryCreate(date=clock.today_local(), status="sober", comment="x" * 2000)
    with pytest.raises(ValidationError):
        EntryCreate(date=clock.today_local(), status="sober", comment="x" * 2001)


def test_date_validation_uses_service_clock(monkeypatch):
    instant = dt.datetime(2026, 10, 29, 22, 30, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(clock, "utc_now", lambda: instant)
    assert EntryCreate(date=dt.date(2026, 10, 30), status="sober")
    with pytest.raises(ValidationError):
        EntryCreate(date=dt.date(2026, 10, 31), status="sober")
