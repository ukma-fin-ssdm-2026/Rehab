import pytest


from backend.app.services.formatting import format_days


@pytest.mark.parametrize(
    "n, expected",
    [
        (1, "1 день"),
        (2, "2 дні"),
        (5, "5 днів"),
        (11, "11 днів"),
        (12, "12 днів"),
        (21, "21 день"),
        (101, "101 день"),
        (111, "111 днів"),
    ],
)
def test_days_use_correct_ukrainian_form(n, expected):
    result = format_days(n)
    assert result == expected
