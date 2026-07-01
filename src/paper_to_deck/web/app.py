from __future__ import annotations

"""FastAPI backend application for the web interface.

Handles file uploads, AI estimation, and triggers the ADK pipeline.
"""

import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from ..security import safe_join
from .runner import run_pipeline

MAX_PDF_BYTES = 25 * 1024 * 1024
_STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Paper to Deck")


def _sandbox() -> Path:
    root = os.environ.get("PAPER_TO_DECK_SANDBOX")
    if not root:
        raise RuntimeError("PAPER_TO_DECK_SANDBOX not set")
    p = Path(root)
    (p / "assets").mkdir(parents=True, exist_ok=True)
    return p


def validate_pdf(data: bytes) -> None:
    # Validates file size against a 25 MB cap to prevent denial-of-service and memory exhaustion.
    if not data or len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="PDF is empty or larger than 25 MB.")
    # Strict %PDF- magic-byte check ensures the file is truly a PDF, not just renamed.
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="That file is not a PDF.")


import json
import fitz
from google import genai
from google.genai import types

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (_STATIC / "index.html").read_text(encoding="utf-8")

@app.post("/estimate")
async def estimate(
    pdf: UploadFile = File(...),
    audience: str = Form(""),
    focus: str = Form(""),
) -> JSONResponse:
    data = await pdf.read()
    validate_pdf(data)
    
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        text = ""
        for i in range(min(3, len(doc))):
            text += doc[i].get_text()
        doc.close()
    except Exception:
        text = "Could not parse PDF text."

    prompt = f"""You are an expert presentation coach.
Based on the first few pages of this research paper, the target audience, and the core focus, 
estimate the optimal talk length (in minutes) and the number of slides needed.
Audience: {audience or 'General audience'}
Core focus: {focus or 'General overview'}

Paper text (first 3 pages):
{text}

Output ONLY a valid JSON object matching this schema:
{{
  "minutes": int, // Suggested talk length
  "slides": int, // Suggested number of main slides (usually 1 slide per 1-1.5 minutes)
  "audience": str // A refined version of the audience if it was empty
}}"""

    client = genai.Client()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        result = json.loads(response.text)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/generate")
async def generate(
    pdf: UploadFile = File(...),
    minutes: str = Form("15"),
    slides: str = Form("10"),
    audience: str = Form("general technical"),
    focus: str = Form(""),
    theme: str = Form("white"),
    font: str = Form("default"),
    flowcharts: bool = Form(False),
) -> JSONResponse:
    data = await pdf.read()
    validate_pdf(data)
    sandbox = _sandbox()
    pdf_path = safe_join(sandbox, f"upload_{uuid.uuid4().hex}.pdf")
    pdf_path.write_bytes(data)
    
    # Use fallback defaults if the user left them entirely empty
    constraints = {
        "minutes": int(minutes) if minutes.strip() else 15,
        "slides": int(slides) if slides.strip() else 10,
        "audience": audience.strip() or "general technical",
        "focus": focus.strip(),
        "theme": theme,
        "font": font,
        "want_flowcharts": flowcharts,
    }
    try:
        await run_pipeline(str(pdf_path), constraints)
        deck_file = sandbox / "deck.html"
        if not deck_file.exists():
            raise RuntimeError("Pipeline completed but deck.html was not created. (The LLM may have failed to call the rendering tool.)")
        return JSONResponse({"deck_url": "/deck"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deck", response_class=HTMLResponse)
def deck() -> str:
    deck_file = _sandbox() / "deck.html"
    if not deck_file.exists():
        raise HTTPException(status_code=404, detail="No deck generated yet.")
    return deck_file.read_text(encoding="utf-8")


@app.get("/assets/{name}")
def deck_asset(name: str) -> FileResponse:
    # /assets/{name} is protected by safe_join, strictly preventing path traversal attacks.
    path = safe_join(_sandbox() / "assets", name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="asset not found")
    return FileResponse(path)
