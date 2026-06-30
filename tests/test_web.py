import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from paper_to_deck.web import app as web_app


def test_index_serves_designed_page():
    client = TestClient(web_app.app)
    r = client.get("/")
    assert r.status_code == 200
    assert "Fraunces" in r.text          # cohesive with deck theme
    assert "dropzone" in r.text.lower()


def test_generate_rejects_non_pdf(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_TO_DECK_SANDBOX", str(tmp_path))
    client = TestClient(web_app.app)
    r = client.post("/generate", files={"pdf": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_generate_accepts_pdf_and_runs_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_TO_DECK_SANDBOX", str(tmp_path))

    async def fake_run(pdf_path, constraints):
        (tmp_path / "deck.html").write_text("<html>deck</html>")
        return str(tmp_path / "deck.html")

    monkeypatch.setattr(web_app, "run_pipeline", fake_run)
    client = TestClient(web_app.app)
    r = client.post(
        "/generate",
        files={"pdf": ("p.pdf", b"%PDF-1.4 fake body", "application/pdf")},
        data={"minutes": "15", "audience": "ML researchers", "focus": "method", "flowcharts": "false"},
    )
    assert r.status_code == 200
    assert r.json()["deck_url"] == "/deck"


def test_validate_pdf_rejects_empty_and_oversize():
    with pytest.raises(HTTPException):
        web_app.validate_pdf(b"")
    with pytest.raises(HTTPException):
        web_app.validate_pdf(b"%PDF-" + b"0" * (web_app.MAX_PDF_BYTES + 1))
