from __future__ import annotations

"""Tool endpoints provided to the ADK agents.

Contains the render_deck_tool that binds the outline to the renderer.
"""

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
        
    outline_json = outline_json.strip()
    # Robust JSON extraction (find first '{' and last '}') that tolerates the LLM 
    # wrapping the JSON payload in conversational prose or markdown code blocks.
    start_idx = outline_json.find("{")
    end_idx = outline_json.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        outline_json = outline_json[start_idx:end_idx+1]
        
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
