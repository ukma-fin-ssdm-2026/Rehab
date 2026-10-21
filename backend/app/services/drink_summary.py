
from collections.abc import Iterable
from typing import TypedDict


class Drink(TypedDict):
    type: str
    volume_ml: int


def total_volume_ml(drinks: Iterable[Drink]) -> int:
    """Повертає сумарний об'єм напоїв у мілілітрах."""
    return sum(drink["volume_ml"] for drink in drinks)


def volume_by_type_ml(drinks: Iterable[Drink]) -> dict[str, int]:
    """Повертає сумарний об'єм для кожного типу напоїв."""
    result: dict[str, int] = {}

    for drink in drinks:
        drink_type = drink["type"]
        volume = drink["volume_ml"]

        result[drink_type] = result.get(drink_type, 0) + volume

    return result
