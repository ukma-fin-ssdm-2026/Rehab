"""Перерахунок рекорду та особистих досягнень користувача."""

import datetime as dt

from backend.app.models import DayStatus
from backend.app.services.statistics import count_streaks


def recompute_progress(db, user_id: int, today: dt.date) -> None:
    """Оновлює кеш рекорду й ознаки досягнення за історією календаря.

    Зміни залишаються в транзакції виклику. Функція не виконує commit.
    """

    from backend.app.repositories.entries import list_user_entries
    from backend.app.repositories.goals import list_user_goals
    from backend.app.repositories.users import get_user

    user = get_user(db, user_id)
    if user is None:
        raise LookupError(f"Користувача {user_id} не знайдено")

    tracking_start_date = user.tracking_start_date
    if tracking_start_date > today:
        raise ValueError("Дата початку відстеження не може бути в майбутньому")

    relapse_dates = {
        entry.date
        for entry in list_user_entries(db, user_id)
        if (
            entry.status == DayStatus.relapse
            and tracking_start_date <= entry.date <= today
        )
    }
    current_streak, longest_streak = count_streaks(
        start_date=tracking_start_date,
        end_date=today,
        relapse_dates=relapse_dates,
    )

    user.best_streak = longest_streak
    for goal in list_user_goals(db, user_id):
        goal.is_achieved = longest_streak >= goal.target_days
        goal.progress_days = (
            goal.target_days
            if goal.is_achieved
            else min(current_streak, goal.target_days)
        )

