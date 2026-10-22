"""Форматування кількості днів українською (1 день, 2 дні, 5 днів)."""


def _day_word(n: int) -> str:
    if 11 <= n % 100 <= 14:
        return "днів"
    last = n % 10
    if last == 1:
        return "день"
    if 2 <= last <= 4:
        return "дні"
    return "днів"


def format_days(n: int) -> str:
    return f"{n} {_day_word(n)}"
