from backend.app.services.formatting import _day_word


def format_progress_days(days: int) -> str:
    if not isinstance(days, int) or isinstance(days, bool):
        raise TypeError("days must be an integer")
    if days < 0:
        raise ValueError("Кількість днів не може бути від'ємною")

    return f"{days} {_day_word(days)}"
