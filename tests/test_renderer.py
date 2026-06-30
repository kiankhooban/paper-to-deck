import pytest
from paper_to_deck.schemas import DeckOutline, Slide
from paper_to_deck.renderer import render_deck
from paper_to_deck.security import UnsafeAssetError


def _outline_with(slide: Slide) -> DeckOutline:
    return DeckOutline(title="T", slides=[slide])


def test_render_escapes_injected_text():
    html = render_deck(_outline_with(Slide(title="<script>x</script>", bullets=["<b>hi</b>"])))
    assert "<script>x</script>" not in html.split("reveal.js")[0]  # not injected raw before framework
    assert "&lt;script&gt;x&lt;/script&gt;" in html
    assert "&lt;b&gt;hi&lt;/b&gt;" in html


def test_render_includes_validated_image():
    slide = Slide(title="Fig", bullets=[], image_id="assets/fig_1.png")
    html = render_deck(_outline_with(slide))
    assert '<img src="assets/fig_1.png"' in html


def test_render_rejects_unsafe_image():
    slide = Slide(title="Bad", bullets=[], image_id="javascript:alert(1)")
    with pytest.raises(UnsafeAssetError):
        render_deck(_outline_with(slide))


def test_appendix_slides_marked_hidden():
    outline = DeckOutline(
        title="T",
        slides=[
            Slide(title="Main", bullets=["a"], section="main"),
            Slide(title="Deep Math", bullets=["b"], section="appendix"),
        ],
    )
    html = render_deck(outline)
    assert 'data-visibility="hidden"' in html
    assert "Deep Math" in html


def test_render_uses_custom_theme_not_default():
    html = render_deck(DeckOutline(title="My Paper", slides=[Slide(title="Intro", bullets=["a"])]))
    # default reveal theme is gone; our design tokens and fonts are present
    assert "theme/white.css" not in html
    assert "Fraunces" in html and "Hanken Grotesk" in html
    assert "#E2552B" in html  # accent token inlined from theme.css


def test_render_emits_title_slide():
    html = render_deck(DeckOutline(title="My Paper", slides=[Slide(title="Intro", bullets=["a"])]))
    assert 'class="title-slide"' in html
    assert "My Paper" in html


def test_render_loads_mathjax():
    html = render_deck(DeckOutline(title="T", slides=[Slide(title="Eq", bullets=["x"])]))
    assert "mathjax" in html.lower()


def test_render_emits_appendix_divider():
    outline = DeckOutline(
        title="T",
        slides=[
            Slide(title="Main", bullets=["a"], section="main"),
            Slide(title="Proof", bullets=["b"], section="appendix"),
        ],
    )
    html = render_deck(outline)
    assert 'class="divider-slide"' in html
