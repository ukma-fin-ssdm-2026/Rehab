from backend.app.services.formatting import format_days


def test_one_day_uses_singular_form():
    days = 1
    result = format_days(days)
    assert result == "1 день"

def test_two_days_use_dni_form():
    assert format_days(2) == "2 дні" 