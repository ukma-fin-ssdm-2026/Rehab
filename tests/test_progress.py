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

@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (0, "0 днів"),
        (4, "4 дні"),
        (5, "5 днів"),
        (11, "11 днів"),
        (21, "21 день"),
        (22, "22 дні"),
        (25, "25 днів"),
    ],
)
def test_format_progress_days_boundaries(days, expected):
    assert format_progress_days(days) == expected

def test_format_progress_days_rejects_string():
    with pytest.raises(TypeError, match="days must be an integer"):
        format_progress_days("3")("3")