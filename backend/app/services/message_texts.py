"""Deterministic automatic copy. User-authored support text is never transformed."""

import json
from functools import lru_cache
from pathlib import Path

STYLES = ("formal", "humorous", "zen", "strict")


@lru_cache(maxsize=1)
def _variants():
    return json.loads(
        Path(__file__).with_name("message_variants.json").read_text(encoding="utf-8")
    )


def render_message(
    message_key: str, style: str, context: dict[str, str], variation: int = 0
) -> tuple[str, str]:
    """Return plain title/body; reject unknown styles, keys and missing context."""
    if style not in STYLES:
        raise ValueError("Невідомий стиль повідомлень")
    choices = _variants()[message_key][style]
    title, body = choices[variation % len(choices)]
    return title.format_map(context), body.format_map(context)
