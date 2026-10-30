"""Форматування кількості днів українською (1 день, 2 дні, 5 днів)."""

# AI-GENERATED START
# Лаб 8: Replace Magic Number with Constant + Decompose Conditional.
# Порівняння ті самі, що й раніше, тож результат для будь-якого n не змінився.
TEENS_FIRST = 11  # 11–14 завжди «днів»: 11 днів, 112 днів
TEENS_LAST = 14
FEW_FIRST = 2  # закінчення 2–4: 2 дні, 23 дні
FEW_LAST = 4
ONE = 1  # закінчення 1: 1 день, 21 день


def _is_teen(n: int) -> bool:
    return TEENS_FIRST <= n % 100 <= TEENS_LAST


def _day_word(n: int) -> str:
    if _is_teen(n):
        return "днів"
    last_digit = n % 10
    if last_digit == ONE:
        return "день"
    if FEW_FIRST <= last_digit <= FEW_LAST:
        return "дні"
    return "днів"


# AI-GENERATED END


def format_days(n: int) -> str:
    return f"{n} {_day_word(n)}"
