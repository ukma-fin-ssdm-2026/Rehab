"""Тести автоматичного підрахунку тверезих днів."""

import datetime as dt

import pytest

from backend.app.services.sobriety import count_sober_days


def test_all_days_are_sober():
    """Усі дні без вживання вважаються тверезими."""

    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [],
    )

    assert result == 7


def test_relapse_days_are_excluded():
    """Дні вживання не входять до кількості тверезих."""

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
    """Повторення однієї дати не змінює результат."""

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
    """Дати вживання поза періодом не враховуються."""

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
    """Один календарний день також враховується."""

    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 1),
        [],
    )

    assert result == 1


def test_end_date_before_start_date():
    """Неправильний діапазон викликає помилку."""

    with pytest.raises(ValueError):
        count_sober_days(
            dt.date(2026, 10, 7),
            dt.date(2026, 10, 1),
            [],
        )

def test_relapse_on_first_day():
    """Вживання в перший день періоду не рахується як тверезий день."""
    result = count_sober_days(
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 7),
        [dt.date(2026, 10, 1)],
    )

    assert result == 6

def test_leap_year_february():
    """Враховує 29 лютого у високосному році."""
    result = count_sober_days(
        dt.date(2024, 2, 28),
        dt.date(2024, 3, 1),
        [dt.date(2024, 2, 29)],
    )

    assert result == 2

def test_relapse_dates_from_generator():
    """Коректно обробляє дати вживання, передані генератором."""
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