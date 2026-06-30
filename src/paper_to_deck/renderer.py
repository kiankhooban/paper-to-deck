from __future__ import annotations

from pathlib import Path

from .schemas import DeckOutline, Slide
from .security import escape_text, safe_asset_src

_REVEAL = "https://cdn.jsdelivr.net/npm/reveal.js@5/dist"
_FONTS = (
    "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600"
    "&family=Hanken+Grotesk:wght@400;600&family=JetBrains+Mono:wght@500&display=swap"
)
_MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"

_THEME_CSS = (Path(__file__).parent / "theme.css").read_text(encoding="utf-8")


def _footer(deck_title: str) -> str:
    t = escape_text(deck_title)
    return f'<div class="deck-footer"><span>{t}</span><span class="slide-num"></span></div>'


def _figure(slide: Slide) -> str:
    src = safe_asset_src(slide.image_id)
    cap = escape_text(slide.caption_text()) if hasattr(slide, "caption_text") else ""
    return f'<figure><img src="{src}"/><figcaption>{cap}</figcaption></figure>'


def _content_slide(slide: Slide, deck_title: str, hidden: bool) -> str:
    attrs = ' data-visibility="hidden"' if hidden else ""
    head = f"<h2>{escape_text(slide.title)}</h2>"
    bullets = ""
    if slide.bullets:
        items = "".join(f"<li>{escape_text(b)}</li>" for b in slide.bullets)
        bullets = f"<ul>{items}</ul>"
    notes = f'<aside class="notes">{escape_text(slide.notes)}</aside>' if slide.notes else ""
    if slide.image_id:
        src = safe_asset_src(slide.image_id)
        body = (
            f'<div class="two-col"><div>{bullets}</div>'
            f'<figure><img src="{src}"/></figure></div>'
        )
    else:
        body = bullets
    return f"<section{attrs}>{head}{body}{notes}{_footer(deck_title)}</section>"


def _title_slide(deck_title: str) -> str:
    t = escape_text(deck_title)
    return (
        '<section class="title-slide">'
        '<div class="kicker">Paper to Deck</div>'
        f"<h1>{t}</h1>"
        '<div class="accent-rule"></div>'
        "</section>"
    )


def _divider_slide(label: str) -> str:
    return (
        '<section class="divider-slide" data-visibility="hidden">'
        '<div class="numeral">&infin;</div>'
        f"<h2>{escape_text(label)}</h2></section>"
    )


def render_deck(outline: DeckOutline) -> str:
    title = escape_text(outline.title)
    main = "".join(_content_slide(s, outline.title, hidden=False) for s in outline.main_slides())
    appendix_slides = outline.appendix_slides()
    appendix = ""
    if appendix_slides:
        appendix = _divider_slide("Appendix: deep dive and Q&A")
        appendix += "".join(
            _content_slide(s, outline.title, hidden=True) for s in appendix_slides
        )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="stylesheet" href="{_FONTS}"/>
<link rel="stylesheet" href="{_REVEAL}/reveal.css"/>
<style>{_THEME_CSS}</style>
</head>
<body>
<div class="reveal"><div class="slides">{_title_slide(outline.title)}{main}{appendix}</div></div>
<script src="{_REVEAL}/reveal.js"></script>
<script id="MathJax-script" async src="{_MATHJAX}"></script>
<script>Reveal.initialize({{ transition: "fade", slideNumber: "c/t" }});</script>
</body>
</html>"""
