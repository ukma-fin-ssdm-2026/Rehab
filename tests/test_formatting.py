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


# AI-GENERATED START
# Характеризаційні тести (Лаб 8): фіксують поточну поведінку перед рефакторингом,
# зокрема незвичну для від'ємних чисел.
@pytest.mark.parametrize(
    "n, expected",
    [
        (0, "0 днів"),
        (3, "3 дні"),
        (4, "4 дні"),
        (10, "10 днів"),
        (13, "13 днів"),
        (14, "14 днів"),
        (15, "15 днів"),
        (20, "20 днів"),
        (22, "22 дні"),
        (24, "24 дні"),
        (25, "25 днів"),
        (100, "100 днів"),
        (112, "112 днів"),
        (114, "114 днів"),
        (115, "115 днів"),
        (1000, "1000 днів"),
        (1001, "1001 день"),
        (1011, "1011 днів"),
        (1021, "1021 день"),
        (-1, "-1 днів"),
        (-2, "-2 днів"),
        (-11, "-11 днів"),
    ],
)
def test_format_days_characterization(n, expected):
    assert format_days(n) == expected


# AI-GENERATED END
