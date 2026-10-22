from backend.app.services.formatting import format_days


def test_one_day_uses_singular_form():
    days = 1
    result = format_days(days)
    assert result == "1 день"