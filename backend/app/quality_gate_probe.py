"""Тимчасова демонстрація Lab08; не імпортується застосунком."""

# За моїм завданням Codex підготував приклад для перевірки Quality Gate.


def summarize_probe_alpha(values: list[int]) -> dict[str, int]:
    total = sum(values)
    count = len(values)
    minimum = min(values, default=0)
    maximum = max(values, default=0)
    spread = maximum - minimum
    weighted = total * count
    adjusted = weighted + spread
    positive = max(adjusted, 0)
    bounded = min(positive, 1000)
    return {
        "total": total,
        "count": count,
        "minimum": minimum,
        "maximum": maximum,
        "spread": spread,
        "weighted": weighted,
        "adjusted": adjusted,
        "positive": positive,
        "bounded": bounded,
    }


def summarize_probe_beta(values: list[int]) -> dict[str, int]:
    total = sum(values)
    count = len(values)
    minimum = min(values, default=0)
    maximum = max(values, default=0)
    spread = maximum - minimum
    weighted = total * count
    adjusted = weighted + spread
    positive = max(adjusted, 0)
    bounded = min(positive, 1000)
    return {
        "total": total,
        "count": count,
        "minimum": minimum,
        "maximum": maximum,
        "spread": spread,
        "weighted": weighted,
        "adjusted": adjusted,
        "positive": positive,
        "bounded": bounded,
    }
