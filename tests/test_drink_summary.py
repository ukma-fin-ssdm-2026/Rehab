from backend.app.services.drink_summary import (
    total_volume_ml,
    volume_by_type_ml,
)


def test_total_volume_of_multiple_drinks():
    drinks = [
        {"type": "beer", "volume_ml": 330},
        {"type": "wine", "volume_ml": 150},
    ]

    result = total_volume_ml(drinks)

    assert result == 480


def test_volume_is_grouped_by_drink_type():
    drinks = [
        {"type": "beer", "volume_ml": 330},
        {"type": "wine", "volume_ml": 150},
        {"type": "beer", "volume_ml": 500},
    ]

    result = volume_by_type_ml(drinks)

    assert result == {
        "beer": 830,
        "wine": 150,
    }
