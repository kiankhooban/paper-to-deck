import fitz  # PyMuPDF
import pytest


@pytest.fixture
def sample_pdf(tmp_path):
    """A 1-page PDF with a title, body text, a drawn figure box, and a 'Figure 1' caption."""
    doc = fitz.open()
    page = doc.new_page(width=400, height=600)
    page.insert_text((50, 50), "Deep Nets for Toast", fontsize=18)
    page.insert_text((50, 100), "We study toast. Toast is bread plus heat.", fontsize=11)
    # a visible figure region
    page.draw_rect(fitz.Rect(50, 150, 350, 350), color=(0, 0, 0), fill=(0.8, 0.8, 0.8))
    page.insert_text((50, 370), "Figure 1: Our toast pipeline overview.", fontsize=10)
    out = tmp_path / "paper.pdf"
    doc.save(out)
    doc.close()
    return out
