"""тести підрахунку днів до наступної цілі"""
from backend.app.services import statistics


def test_one_day_left_to_first_goal():
    assert statistics.get_days_remaining(6) == 1