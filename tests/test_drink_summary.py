
from backend.app.services.drink_summary import total_volume_ml


def test_total_volume_of_multiple_drinks():
    drinks = [
        {"type": "beer", "volume_ml": 330},
        {"type": "wine", "volume_ml": 150},
    ]

    result = total_volume_ml(drinks)

    assert result == 480
