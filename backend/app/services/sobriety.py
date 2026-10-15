"""Розрахунок тверезих днів за календарними датами."""

import datetime as dt
from collections.abc import Iterable


def count_sober_days(
    start_date: dt.date,
    end_date: dt.date,
    relapse_dates: Iterable[dt.date],
) -> int:
    """Рахує тверезі дні у включному діапазоні дат.

    Дні без запису про вживання вважаються тверезими.
    Дати вживання враховуються лише один раз.
    """

    if end_date < start_date:
        raise ValueError("Кінцева дата не може бути раніше початкової")

    total_days = (end_date - start_date).days + 1

    relapses_in_period = {day for day in relapse_dates if start_date <= day <= end_date}

    return total_days - len(relapses_in_period)
