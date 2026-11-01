"""Розрахунок статистики тверезості для прототипу Rehab.

Усі показники обчислюються з календарних записів.
Дні без запису після початку відстеження вважаються тверезими.
"""

import datetime as dt
from collections.abc import Iterable
from typing import Literal

from backend.app.models import DayStatus, EntryOut, TriggerCategory
from backend.app.services.sobriety import count_sober_days

StatisticsPeriod = Literal["all", "week", "month", "year"]

VALID_PERIODS = ("all", "week", "month", "year")
FIXED_GOAL_DAYS = (7, 30, 90, 180, 365)


def calculate_goal_progress(
    *,
    current_streak: int,
    longest_streak: int,
) -> tuple[bool, int | None, list[int], int]:
    """Обчислює фіксовані етапи 7, 30, 90, 180 і 365 днів.

    Історичне виконання визначається за найдовшою серією, а видимий
    прогрес активного етапу — за поточною. Етапи належать застосунку,
    тому їх наявність не залежить від записів у таблиці цілей.
    """

    if current_streak < 0 or longest_streak < 0:
        raise ValueError("Серія тверезості не може бути від'ємною")
    if current_streak > longest_streak:
        raise ValueError("Поточна серія не може перевищувати рекорд")

    completed_goal_days = sorted(
        days for days in FIXED_GOAL_DAYS if longest_streak >= days
    )
    active_goal_days = next(
        (days for days in FIXED_GOAL_DAYS if longest_streak < days),
        None,
    )
    goal_progress_days = (
        min(current_streak, active_goal_days) if active_goal_days is not None else 0
    )

    return (
        True,
        active_goal_days,
        completed_goal_days,
        goal_progress_days,
    )


def get_period_start(
    period: StatisticsPeriod,
    tracking_start_date: dt.date,
    today: dt.date,
) -> dt.date:
    """Визначає початок періоду з урахуванням старту відстеження."""

    if period == "all":
        requested_start = tracking_start_date
    elif period == "week":
        requested_start = today - dt.timedelta(days=6)
    elif period == "month":
        requested_start = today.replace(day=1)
    elif period == "year":
        requested_start = today.replace(month=1, day=1)
    else:
        raise ValueError(f"Невідомий період статистики: {period}")

    return max(requested_start, tracking_start_date)


def count_streaks(
    start_date: dt.date,
    end_date: dt.date,
    relapse_dates: Iterable[dt.date],
) -> tuple[int, int]:
    """Повертає поточну та найдовшу серію тверезих днів.

    Серія переривається в день вживання алкоголю.
    Якщо сьогодні був зрив, поточна серія дорівнює нулю.
    """

    if end_date < start_date:
        raise ValueError("Кінцева дата не може бути раніше початкової")

    relapses = set(relapse_dates)

    current_streak = 0
    longest_streak = 0

    day = start_date

    while day <= end_date:
        if day in relapses:
            current_streak = 0
        else:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)

        day += dt.timedelta(days=1)

    return current_streak, longest_streak


def calculate_statistics(
    *,
    tracking_start_date: dt.date,
    today: dt.date,
    entries: Iterable[EntryOut],
    period: StatisticsPeriod = "all",
) -> dict[str, object]:
    """Обчислює статистику за погодженим API-контрактом.

    entries повинні містити записи лише потрібного користувача.
    Фільтрацію за user_id виконує API-роутер.

    Показники sober_days і relapse_days залежать від period.
    Загальна кількість днів, серії та цілі рахуються за весь
    період від початку відстеження до сьогодні.
    """

    if period not in VALID_PERIODS:
        raise ValueError(f"Невідомий період статистики: {period}")

    if tracking_start_date > today:
        raise ValueError("Дата початку відстеження не може бути в майбутньому")

    period_start = get_period_start(
        period=period,
        tracking_start_date=tracking_start_date,
        today=today,
    )

    relapse_dates = {
        entry.date
        for entry in entries
        if (
            entry.status == DayStatus.relapse
            and tracking_start_date <= entry.date <= today
        )
    }

    relapses_in_period = {day for day in relapse_dates if period_start <= day <= today}

    sober_days = count_sober_days(
        start_date=period_start,
        end_date=today,
        relapse_dates=relapse_dates,
    )

    total_sober_days = count_sober_days(
        start_date=tracking_start_date,
        end_date=today,
        relapse_dates=relapse_dates,
    )

    current_streak, longest_streak = count_streaks(
        start_date=tracking_start_date,
        end_date=today,
        relapse_dates=relapse_dates,
    )

    has_goals, active_goal_days, completed_goal_days, goal_progress_days = (
        calculate_goal_progress(
            current_streak=current_streak,
            longest_streak=longest_streak,
        )
    )

    return {
        "period": period,
        "tracking_start_date": tracking_start_date,
        "period_start": period_start,
        "period_end": today,
        "sober_days": sober_days,
        "relapse_days": len(relapses_in_period),
        "total_sober_days": total_sober_days,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "active_goal_days": active_goal_days,
        "has_goals": has_goals,
        "completed_goal_days": completed_goal_days,
        "goal_progress_days": goal_progress_days,
    }


def get_days_remaining(sober_days: int) -> int:
    if sober_days < 0:
        raise ValueError("Кількість тверезих днів не може бути від'ємною")

    for goal in FIXED_GOAL_DAYS:
        if sober_days < goal:
            return goal - sober_days

    return 0


def calculate_trigger_distribution(
    entries: Iterable[EntryOut], *, today: dt.date
) -> dict[str, object]:
    """Повертає анонімний розподіл категорій зривів за останні 30 днів."""
    period_start = today - dt.timedelta(days=29)
    counts = {category.value: 0 for category in TriggerCategory}
    for entry in entries:
        if (
            entry.status == DayStatus.relapse
            and entry.trigger_category is not None
            and period_start <= entry.date <= today
        ):
            counts[entry.trigger_category.value] += 1

    total = sum(counts.values())
    categories = []
    for category, count in counts.items():
        percentage = round(count * 100 / total, 1) if total else 0.0
        categories.append(
            {"category": category, "count": count, "percentage": percentage}
        )

    return {
        "period_start": period_start,
        "period_end": today,
        "total": total,
        "categories": categories,
    }
