def format_days(n: int) -> str:
    return f"{n} день"

def format_days(n: int) -> str:
    if n == 1:
        return f"{n} день"
    return f"{n} дні"

def format_days(n: int) -> str:
    if n == 1:
        return f"{n} день"
    if n <= 4:
        return f"{n} дні"
    return f"{n} днів"