from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF

from .schemas import Figure, ParsedPaper
from .security import safe_join

_CAPTION_RE = re.compile(r"^(figure|fig\.?|table)\s+(\d+)", re.IGNORECASE)


def _caption_kind(text: str) -> str:
    return "table" if text.lower().startswith("table") else "figure"


def parse_paper(pdf_path: str, sandbox_root: str) -> ParsedPaper:
    root = Path(sandbox_root)
    # Reject any pdf path that resolves outside the sandbox root.
    pdf = safe_join(root, *Path(pdf_path).resolve().relative_to(root.resolve()).parts) \
        if Path(pdf_path).resolve().is_relative_to(root.resolve()) \
        else safe_join(root, pdf_path)

    assets_dir = safe_join(root, "assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf)
    pages_text: list[str] = []
    figures: list[Figure] = []
    fig_counter = 0

    title = ""
    for page_index, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []  # (rect, text)
        for b in blocks:
            if "lines" not in b:
                continue
            line_text = " ".join(
                span["text"] for line in b["lines"] for span in line["spans"]
            ).strip()
            if line_text:
                text_blocks.append((fitz.Rect(b["bbox"]), line_text))

        pages_text.append("\n".join(t for _, t in text_blocks))

        if page_index == 0 and text_blocks:
            # Heuristic: the largest-font first block is the title.
            title = max(text_blocks[:5], key=lambda tb: tb[0].height)[1]

        # Associate each caption with the nearest image/region directly above it.
        image_rects = [fitz.Rect(img_info["bbox"]) for img_info in page.get_image_info()]
        for rect, text in text_blocks:
            m = _CAPTION_RE.match(text)
            if not m:
                continue
            fig_counter += 1
            fig_id = f"fig_{fig_counter}"
            clip = _region_above_caption(rect, image_rects, page.rect)
            pix = page.get_pixmap(clip=clip, dpi=150)
            out_path = safe_join(assets_dir, f"{fig_id}.png")
            pix.save(out_path)
            figures.append(
                Figure(
                    id=fig_id,
                    kind=_caption_kind(text),
                    caption=text,
                    image_path=f"assets/{fig_id}.png",
                    page=page_index + 1,
                )
            )

    doc.close()
    return ParsedPaper(
        title=title or "Untitled Paper",
        full_text="\n\n".join(pages_text),
        pages=pages_text,
        figures=figures,
    )


def _region_above_caption(caption_rect, image_rects, page_rect):
    """Pick the image rect whose bottom is closest above the caption; else a band above it."""
    above = [r for r in image_rects if r.y1 <= caption_rect.y0 + 5]
    if above:
        nearest = min(above, key=lambda r: caption_rect.y0 - r.y1)
        return nearest
    # Fallback: a fixed band of the page above the caption.
    top = max(page_rect.y0, caption_rect.y0 - 220)
    return fitz.Rect(page_rect.x0 + 20, top, page_rect.x1 - 20, caption_rect.y0 - 2)
