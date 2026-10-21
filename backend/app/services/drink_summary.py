
from collections.abc import Iterable
from typing import Any


def total_volume_ml(drinks: Iterable[dict[str, Any]]) -> int:
    """Повертає сумарний об'єм напоїв у мілілітрах."""
    return sum(drink["volume_ml"] for drink in drinks)
