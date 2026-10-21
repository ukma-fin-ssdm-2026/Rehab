import pytest

from backend.app.services.progress import format_progress_days


def test_format_progress_days_one():
    assert format_progress_days(1) == "1 день"


def test_format_progress_days_few():
    assert format_progress_days(3) == "3 дні"


def test_format_progress_days_many():
    assert format_progress_days(8) == "8 днів"


def test_format_progress_days_rejects_negative():
    with pytest.raises(ValueError):
        format_progress_days(-1)