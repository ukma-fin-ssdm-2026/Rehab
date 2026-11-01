import pytest
from pydantic import ValidationError
from backend.app.schemas.notifications import SupportCommentCreate


def test_support_text_is_trimmed_but_not_html_interpreted():
    assert SupportCommentCreate(text="  <b>Тримайся</b>  ").text == "<b>Тримайся</b>"
    assert len(SupportCommentCreate(text="🙂" * 2000).text) == 2000


@pytest.mark.parametrize(
    "data",
    [
        {"text": "   "},
        {"text": "x" * 2001},
        {"text": 1},
        {"text": "ok", "author_id": 1},
        {"text": "ok", "recipient_id": 2},
    ],
)
def test_invalid_text_and_spoofed_ownership_are_rejected(data):
    with pytest.raises(ValidationError):
        SupportCommentCreate(**data)
