from pathlib import Path

import pytest
from paper_to_deck.pdf_parser import parse_paper
from paper_to_deck.security import PathTraversalError


def test_parse_extracts_text_and_title(sample_pdf, tmp_path):
    result = parse_paper(str(sample_pdf), sandbox_root=str(tmp_path))
    assert "toast" in result.full_text.lower()
    assert result.title.strip() != ""


def test_parse_detects_figure_and_writes_asset(sample_pdf, tmp_path):
    result = parse_paper(str(sample_pdf), sandbox_root=str(tmp_path))
    assert len(result.figures) >= 1
    fig = result.figures[0]
    assert fig.kind == "figure"
    assert fig.caption.lower().startswith("figure 1")
    assert fig.image_path.startswith("assets/")
    assert (tmp_path / fig.image_path).exists()


def test_parse_rejects_pdf_outside_sandbox(tmp_path):
    outside = tmp_path.parent / "evil.pdf"
    with pytest.raises(PathTraversalError):
        parse_paper(str(outside), sandbox_root=str(tmp_path))
