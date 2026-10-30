import json
from pathlib import Path

import pytest

from backend.app.services.message_texts import render_message

ROOT = Path(__file__).resolve().parents[1]


def test_server_and_client_catalogs_match_and_cover_all_styles():
    server = json.loads(
        (ROOT / "backend/app/services/message_catalog.json").read_text(encoding="utf-8")
    )
    client = json.loads(
        (ROOT / "frontend/src/messages/catalog-data.json").read_text(encoding="utf-8")
    )
    assert server == client
    assert set(server) == {
        "home.motivation",
        "goals.motivation",
        "calendar.empty",
        "statistics.empty",
        "support.empty",
        "daily_reminder",
        "relapse",
        "relapse.corrected",
        "support_comment",
    }
    for key, styles in server.items():
        assert set(styles) == {"formal", "humorous", "zen", "strict"}
        for style in styles:
            title, body = render_message(
                key, style, {"nickname": "<b>Оля</b>", "date": "2026-10-30"}
            )
            assert title and body
            assert "{nickname}" not in body
            if key == "relapse":
                assert "<b>Оля</b>" in body
                assert "2026-10-30" in body


@pytest.mark.parametrize("style", ["formal", "humorous", "zen", "strict"])
def test_reminder_keeps_default_sober_and_calendar_instruction(style):
    _, body = render_message("daily_reminder", style, {})
    assert "тверезий день" in body
    assert "зрив" in body
    assert "календар" in body


def test_invalid_key_style_and_missing_context_are_not_silent():
    with pytest.raises(KeyError):
        render_message("unknown", "formal", {})
    with pytest.raises(ValueError):
        render_message("home.motivation", "unknown", {})
    with pytest.raises(KeyError):
        render_message("relapse", "formal", {})
