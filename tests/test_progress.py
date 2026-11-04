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


# За моїм завданням Codex додав граничні тести відмінювання.
# Я вручну звірила в PowerShell результати для 1, 3, 12, 112 і 1001.
@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (0, "0 днів"),
        (4, "4 дні"),
        (5, "5 днів"),
        (11, "11 днів"),
        (12, "12 днів"),
        (13, "13 днів"),
        (14, "14 днів"),
        (21, "21 день"),
        (22, "22 дні"),
        (25, "25 днів"),
        (112, "112 днів"),
        (113, "113 днів"),
        (114, "114 днів"),
        (1001, "1001 день"),
    ],
)
def test_format_progress_days_boundaries(days, expected):
    assert format_progress_days(days) == expected


def test_format_progress_days_rejects_string():
    with pytest.raises(TypeError, match="days must be an integer"):
        format_progress_days("3")


def test_format_progress_days_rejects_boolean():
    with pytest.raises(TypeError, match="days must be an integer"):
        format_progress_days(True)


# За моїм завданням Codex додав перевірки bool, float і None.
# Я вручну перевірила TypeError для True, 3.0, None та ValueError для -1 у PowerShell.
@pytest.mark.parametrize("days", [False, 3.0, -1.0, None])
def test_format_progress_days_rejects_non_integer_values(days):
    with pytest.raises(TypeError, match="days must be an integer"):
        format_progress_days(days)
