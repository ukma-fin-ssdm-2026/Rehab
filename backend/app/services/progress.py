def format_progress_days(days: int) -> str:
    if not isinstance(days, int) or isinstance(days, bool):
        raise TypeError("days must be an integer")
    if days < 0:
        raise ValueError("Кількість днів не може бути від'ємною")

    if days % 10 == 1 and days % 100 != 11:
        word = "день"
    elif days % 10 in (2, 3, 4) and days % 100 not in (12, 13, 14):
        word = "дні"
    else:
        word = "днів"

    return f"{days} {word}"