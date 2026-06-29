from __future__ import annotations

import os
from pathlib import Path

from pydantic import ValidationError

from ..renderer import render_deck
from ..schemas import DeckOutline
from ..security import safe_join


def render_deck_tool(outline_json: str) -> str:
    """Render a DeckOutline JSON string into a sanitized Reveal.js deck.

    Returns the absolute path to deck.html, or a string starting with 'ERROR' on bad input.
    """
    root = os.environ.get("PAPER_TO_DECK_SANDBOX")
    if not root:
        return "ERROR: PAPER_TO_DECK_SANDBOX is not set"
    try:
        outline = DeckOutline.model_validate_json(outline_json)
    except ValidationError as exc:
        return f"ERROR: invalid outline JSON: {exc.error_count()} errors"
    except ValueError as exc:
        return f"ERROR: invalid outline JSON: {exc}"
    html = render_deck(outline)
    out_path = safe_join(Path(root), "deck.html")
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)
