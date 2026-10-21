
from collections.abc import Iterable
from typing import TypedDict


class Drink(TypedDict):
    type: str
    volume_ml: int


def total_volume_ml(drinks: Iterable[Drink]) -> int:
    """Повертає сумарний об'єм напоїв у мілілітрах."""
    return sum(drink["volume_ml"] for drink in drinks)
