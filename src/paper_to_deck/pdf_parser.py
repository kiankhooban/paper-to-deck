"""PDF processing and vision extraction logic.

Uses PyMuPDF to extract text and captions, and Gemini Vision to map out
figure bounding boxes.
"""
import os
import re
import json
from pathlib import Path
import fitz  # PyMuPDF
from google import genai
from google.genai.types import Part

from .schemas import Figure, ParsedPaper
from .security import safe_join

_CAPTION_RE = re.compile(r"^(figure|fig\.?|table)\s+(\d+)", re.IGNORECASE)

def _caption_kind(text: str | None) -> str:
    if not text:
        return "figure"
    return "table" if text.lower().startswith("table") else "figure"

def _get_gemini_client():
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE":
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
    return genai.Client()

def extract_figures_from_page(pix_bytes: bytes) -> list[dict]:
    client = _get_gemini_client()
    # Gemini vision returns bounding boxes on a 0-1000 normalized scale, which provides 
    # robust layout analysis and precise cropping far beyond what simple regex can achieve.
    prompt = """
    You are an expert layout analysis model. Find all scientific figures, diagrams, and tables in this image.
    Return a JSON array of objects. Each object should have:
    - "type": "figure" or "table"
    - "caption": the exact text of the caption
    - "bbox": [ymin, xmin, ymax, xmax] as integers between 0 and 1000 representing the bounding box of the figure/table ITSELF (strictly excluding the caption and surrounding paragraph text).
    If none are found, return an empty array [].
    """
    model_id = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[Part.from_bytes(data=pix_bytes, mime_type="image/png"), prompt],
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini vision error: {e}")
        return []

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
        has_caption = False
        
        for b in blocks:
            if "lines" not in b:
                continue
            line_text = " ".join(
                span["text"] for line in b["lines"] for span in line["spans"]
            ).strip()
            if line_text:
                text_blocks.append((fitz.Rect(b["bbox"]), line_text))
                if _CAPTION_RE.match(line_text):
                    has_caption = True

        pages_text.append("\n".join(t for _, t in text_blocks))

        if page_index == 0 and text_blocks:
            # Heuristic: the largest-font first block is the title.
            title = max(text_blocks[:5], key=lambda tb: tb[0].height)[1]

        # Only query Gemini if PyMuPDF detected a caption, to save time/cost.
        # This caption-gated call avoids sending text-only pages to the vision model.
        if has_caption:
            # Create a cleaned pixmap for Gemini to avoid sloppy bounding boxes.
            # The body-text white-out trick blanks main-body text before sending the page
            # to Gemini so the model returns tighter figure boxes.
            pix_clean = page.get_pixmap(dpi=150)
            font_sizes = []
            for b in blocks:
                if b.get("type", -1) == 0:
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            font_sizes.append(round(span.get("size", 0), 1))
            
            if font_sizes:
                from collections import Counter
                main_size = Counter(font_sizes).most_common(1)[0][0]
                for b in blocks:
                    if b.get("type", -1) == 0:
                        is_main_text = any(
                            round(span.get("size", 0), 1) == main_size
                            for line in b.get("lines", []) for span in line.get("spans", [])
                        )
                        text = " ".join(span.get("text", "") for line in b.get("lines", []) for span in line.get("spans", [])).strip()
                        if is_main_text and not _CAPTION_RE.match(text):
                            rect = fitz.Rect(b["bbox"]) * (150/72)
                            pix_clean.set_rect(rect, (255, 255, 255))
                            
            fig_data_list = extract_figures_from_page(pix_clean.tobytes("png"))
            
            w = page.rect.width
            h = page.rect.height
            
            for item in fig_data_list:
                bbox = item.get("bbox")
                if not bbox or len(bbox) != 4:
                    continue
                    
                fig_counter += 1
                fig_id = f"fig_{fig_counter}"
                
                # Convert 0-1000 scale to absolute page coordinates
                ymin, xmin, ymax, xmax = bbox
                x0 = w * xmin / 1000.0
                y0 = h * ymin / 1000.0
                x1 = w * xmax / 1000.0
                y1 = h * ymax / 1000.0
                
                clip = fitz.Rect(x0, y0, x1, y1)
                # Expand clip slightly (5pt) to ensure no edges or borders are lost in the crop
                clip = clip + (-5, -5, 5, 5)
                
                # Crop and save
                fig_pix = page.get_pixmap(clip=clip, dpi=150)
                out_path = safe_join(assets_dir, f"{fig_id}.png")
                fig_pix.save(out_path)
                
                figures.append(
                    Figure(
                        id=fig_id,
                        kind=_caption_kind(item.get("caption")),
                        caption=item.get("caption") or "",
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
