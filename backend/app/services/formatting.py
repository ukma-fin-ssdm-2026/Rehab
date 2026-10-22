def format_days(n: int) -> str:
    last = n % 10
    if 11 <= n % 100 <= 14:
        return f"{n} днів"
    if last == 1:
        return f"{n} день"
    if 2 <= last <= 4:
        return f"{n} дні"
    return f"{n} днів"