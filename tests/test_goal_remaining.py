import pytest

from backend.app.services import statistics


def test_one_day_left_to_first_goal():
    assert statistics.get_days_remaining(6) == 1


def test_days_left_to_second_goal():
    assert statistics.get_days_remaining(8) == 22


def test_exactly_seven_sober_days():
    assert statistics.get_days_remaining(7) == 23


def test_thirty_sober_days():
    assert statistics.get_days_remaining(30) == 60


def test_negative_sober_days():
    with pytest.raises(ValueError):
        statistics.get_days_remaining(-1)


@pytest.mark.parametrize(
    ("days", "remaining"),
    [(89, 1), (90, 90), (179, 1), (180, 185), (364, 1), (365, 0), (366, 0)],
)
def test_extended_days_remaining(days, remaining):
    assert statistics.get_days_remaining(days) == remaining
