def format_days(n: int) -> str:
    last = n % 10
    if last == 1:
        return f"{n} день"
    if 2 <= last <= 4:
        return f"{n} дні"
    return f"{n} днів"