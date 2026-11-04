from backend.app.services.formatting import format_days


# За моїм завданням Codex використав format_days, зберігши валідацію.
# Я перевірила виклики в PowerShell: результати й типи помилок збіглися з очікуваними.
def format_progress_days(days: int) -> str:
    if not isinstance(days, int) or isinstance(days, bool):
        raise TypeError("days must be an integer")
    if days < 0:
        raise ValueError("Кількість днів не може бути від'ємною")

    return format_days(days)
