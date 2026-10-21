import datetime as dt

import pytest

from backend.app.services.sobriety import count_sober_days


def test_all_days_are_sober():

    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [],
    )

    assert result == 7


def test_relapse_days_are_excluded():


    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [
            dt.date(2026, 10, 3),
            dt.date(2026, 10, 6),
        ],
    )

    assert result == 5


def test_duplicate_relapse_dates_count_once():


    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [
            dt.date(2026, 10, 3),
            dt.date(2026, 10, 3),
        ],
    )

    assert result == 6


def test_relapses_outside_period_are_ignored():


    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [
            dt.date(2026, 9, 30),
            dt.date(2026, 10, 8),
        ],
    )

    assert result == 7


def test_single_day_period():
  
    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 1),
        [],
    )

    assert result == 1


def test_end_date_before_start_date():
 
    with pytest.raises(ValueError):
        count_sober_days(
            dt.date(2026, 10, 7),
            dt.date(2026, 10, 1),
            [],
        )

def test_relapse_on_first_day():
  
    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [dt.date(2026, 10, 1)],
    )

    assert result == 6

def test_leap_year_february():
   
    result = count_sober_days(
        dt.date(2024, 2, 28),
        dt.date(2024, 3, 1),
        [dt.date(2024, 2, 29)],
    )

    assert result == 2

def test_relapse_dates_from_generator():
   
    relapse_dates = (
        day
        for day in [
            dt.date(2026, 10, 2),
            dt.date(2026, 10, 4),
        ]
    )

    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        relapse_dates,
    )

    assert result == 5

def test_relapse_on_last_day():
    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [dt.date(2026, 10, 7)],
    )

    assert result == 6

def test_invalid_period_error_message():
    with pytest.raises(ValueError) as error:
        count_sober_days(
            dt.date(2026, 10, 7),
            dt.date(2026, 10, 1),
            [],
        )

    assert str(error.value) == "Кінцева дата не може бути раніше початкової"
