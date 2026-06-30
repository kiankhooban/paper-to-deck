from __future__ import annotations

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
    if not data or len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="PDF is empty or larger than 25 MB.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="That file is not a PDF.")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (_STATIC / "index.html").read_text(encoding="utf-8")


@app.post("/generate")
async def generate(
    pdf: UploadFile = File(...),
    minutes: int = Form(15),
    audience: str = Form("general technical"),
    focus: str = Form(""),
    flowcharts: bool = Form(False),
) -> JSONResponse:
    data = await pdf.read()
    validate_pdf(data)
    sandbox = _sandbox()
    pdf_path = safe_join(sandbox, f"upload_{uuid.uuid4().hex}.pdf")
    pdf_path.write_bytes(data)
    constraints = {
        "minutes": minutes,
        "audience": audience,
        "focus": focus,
        "want_flowcharts": flowcharts,
    }
    try:
        await run_pipeline(str(pdf_path), constraints)
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
    path = safe_join(_sandbox() / "assets", name)  # safe_join blocks traversal
    if not path.exists():
        raise HTTPException(status_code=404, detail="asset not found")
    return FileResponse(path)
