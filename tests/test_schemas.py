import pytest
from pydantic import ValidationError
from paper_to_deck.schemas import Figure, ParsedPaper, Slide, DeckOutline


def test_figure_requires_known_kind():
    with pytest.raises(ValidationError):
        Figure(id="f1", kind="diagram", caption="c", image_path="assets/f1.png", page=1)


def test_parsed_paper_round_trips():
    paper = ParsedPaper(
        title="A Paper",
        full_text="body",
        pages=["page one"],
        figures=[Figure(id="f1", kind="figure", caption="Figure 1: x", image_path="assets/f1.png", page=1)],
    )
    assert paper.model_dump()["figures"][0]["id"] == "f1"


def test_deck_outline_splits_main_and_appendix():
    outline = DeckOutline(
        title="Deck",
        slides=[
            Slide(title="Intro", bullets=["a"], section="main"),
            Slide(title="Proof", bullets=["b"], section="appendix"),
        ],
    )
    assert len(outline.main_slides()) == 1
    assert len(outline.appendix_slides()) == 1
    assert outline.appendix_slides()[0].title == "Proof"
