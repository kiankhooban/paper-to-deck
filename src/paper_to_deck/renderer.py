from __future__ import annotations

from .schemas import DeckOutline, Slide
from .security import escape_text, safe_asset_src

_REVEAL_CSS = "https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.css"
_REVEAL_THEME = "https://cdn.jsdelivr.net/npm/reveal.js@5/dist/theme/white.css"
_REVEAL_JS = "https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.js"


def _render_slide(slide: Slide, hidden: bool) -> str:
    attrs = ' data-visibility="hidden"' if hidden else ""
    parts = [f"<section{attrs}>"]
    parts.append(f"<h2>{escape_text(slide.title)}</h2>")
    if slide.image_id:
        src = safe_asset_src(slide.image_id)
        parts.append(f'<img src="{src}" style="max-height:55vh;"/>')
    if slide.bullets:
        parts.append("<ul>")
        parts.extend(f"<li>{escape_text(b)}</li>" for b in slide.bullets)
        parts.append("</ul>")
    if slide.notes:
        parts.append(f"<aside class=\"notes\">{escape_text(slide.notes)}</aside>")
    parts.append("</section>")
    return "".join(parts)


def render_deck(outline: DeckOutline) -> str:
    main = "".join(_render_slide(s, hidden=False) for s in outline.main_slides())
    appendix_inner = "".join(_render_slide(s, hidden=True) for s in outline.appendix_slides())
    # Group the appendix as one vertical stack so it stays out of the linear flow.
    appendix = f"<section{' data-visibility=\"hidden\"' if appendix_inner else ''}>{appendix_inner}</section>" if appendix_inner else ""
    title = escape_text(outline.title)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<link rel="stylesheet" href="{_REVEAL_CSS}"/>
<link rel="stylesheet" href="{_REVEAL_THEME}"/>
</head>
<body>
<div class="reveal"><div class="slides">{main}{appendix}</div></div>
<script src="{_REVEAL_JS}"></script>
<script>Reveal.initialize();</script>
</body>
</html>"""
