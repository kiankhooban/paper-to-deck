# Paper-to-Deck Architect

> Built for the Kaggle 5-Day AI Agents Capstone. 
> Example deck generated from an open-access arXiv paper (citation placeholder).

**Paper-to-Deck Architect instantly transforms dense, 20-page academic research PDFs into beautifully formatted, time-boxed interactive presentation decks for MS/PhD students drowning in papers. You set the talk length (default 15 minutes) and the deck sizes itself to fit.**

![demo](docs/demo.gif)

<div style="display: flex; justify-content: space-between; gap: 10px;">
  <img src="docs/screenshot-upload.png" alt="Upload Interface" width="32%"/>
  <img src="docs/screenshot-deck.png" alt="Main Deck" width="32%"/>
  <img src="docs/screenshot-appendix.png" alt="Hidden Appendix" width="32%"/>
</div>

## The Problem

Turning a dense, highly technical academic paper into a talk-ready presentation is an arduous, multi-hour process. It requires reading deep derivations, manually snipping figures and tables, restructuring complex arguments into digestible bullet points, and laboriously formatting slides. Existing LLM wrappers often fail at this because they lack the ability to physically extract visual elements from the PDF, hallucinate UI code, and struggle to condense content without losing the deep math required for Q&A sessions.

## How It Works

Paper-to-Deck Architect solves this by orchestrating a specialized multi-agent pipeline using a `SequentialAgent` from the Google ADK. State is seamlessly passed between agents via `output_key` routing.

```mermaid
flowchart TD
    A[PDF Upload] --> B(FastAPI Backend)
    B -->|Sandboxed File| C[MCP Server]
    C -->|PyMuPDF Extracts Text & Crops Figures| D[Concierge Agent]
    D -->|User Constraints| E[Distiller Agent]
    E -->|10 Main + 20 Appendix Slides| F[Visual Matcher Agent]
    F -->|Maps Figures to Slides| G[Frontend Coder Agent]
    G -->|Calls render_deck()| H[Reveal.js Output]
```

1. **Upload & Sandbox:** The FastAPI backend securely receives the PDF, validating its `%PDF` magic bytes and enforcing a strict 25MB cap. The file is saved to an isolated, sandboxed path to prevent traversal attacks.
2. **Vision & Crop (MCP Server):** An internal Model Context Protocol (MCP) server runs PyMuPDF to extract raw text and actively crop bounding boxes around figures and tables, saving them to a sandboxed `/assets` folder. It associates captions with images using a `caption-regex` paired with a "nearest-region-above" heuristic—it identifies the caption text block and calculates the distance to the bottom of all image rects above it, snapping the crop to the nearest visual asset.
3. **Concierge Agent:** Interviews the user (or parses form inputs) to establish presentation constraints, including talk duration, target audience, and the core focus of the talk.
4. **Distiller Agent:** Restructures the paper into a strict outline. It produces exactly the number of main slides that fit the requested talk length (roughly one slide per 1–1.5 minutes, estimated from paper density and audience). All heavy mathematical derivations, secondary results, and deep proofs are dynamically routed into a "Hidden Appendix" (up to 20 slides) that stays out of the linear flow but remains accessible during Q&A.
5. **Visual Matcher Agent:** Reviews the generated slide outline and the MCP server's figure manifest, intelligently mapping the perfectly cropped assets to their corresponding slides.
6. **Frontend Coder Agent:** The agent does *not* freehand HTML, which is a massive XSS and hallucination risk. Instead, it calls a deterministic, sanitizing `render_deck` tool that outputs the final, flawless Reveal.js presentation.

## Why The Design Choices Matter

This system was engineered with flaw-first architectural constraints rather than relying purely on LLM instruction-following:
- **Pydantic Literal Schemas:** The LLM's output schema locks the `theme` and `font` fields to strict `Literal` types. This structurally guarantees the agent cannot hallucinate non-existent Reveal.js CSS files that would cause the UI to crash into a white screen.
- **Deterministic Rendering:** The `render_deck` tool is entirely deterministic and XSS-safe. It HTML-escapes all strings before injection, ensuring no invalid markup breaks the presentation structure.
- **Sandboxed Filesystem:** All PDF operations and asset extractions occur within a strict sandbox. Any path that resolves outside the base directory is immediately rejected, neutralizing path traversal vulnerabilities.
- **Unicode Math:** LLMs frequently generate broken LaTeX syntax when injecting directly into HTML templates. The system forces the agent to use clean, robust unicode math (e.g., `α`, `x²`), bypassing fragile web rendering engines like MathJax entirely.
- **The Hidden Appendix Pattern:** Enforcing a strict 10-slide limit prevents the LLM from generating endless, unreadable decks. Stashing the rest of the paper in a vertical Reveal.js stack gives presenters instant access to the dense math they need for aggressive Q&A sessions without bloating the main talk.

## Tech Stack

- **Google ADK (Agent Development Kit):** Provides the robust `SequentialAgent` orchestration and state routing.
- **Gemini 2.5 Flash (Vertex AI):** Lightning-fast intelligence for structuring dense academic text and constraint solving.
- **Model Context Protocol (MCP):** Exposes a standardized tool interface for our internal PyMuPDF asset extraction logic.
- **FastAPI:** Handles robust, asynchronous file uploads and provides a fast web frontend.
- **Reveal.js:** The industry standard for beautiful, HTML-based slide decks.
- **Pydantic v2:** For rigorous schema validation and LLM output parsing.
- **uv:** Ultra-fast, deterministic Python package management.

## Security & Cost Posture

This project is hardened by default and designed for enterprise deployment on Google Cloud.
- **Vertex AI + ADC:** Authentication is handled strictly via Vertex AI and Application Default Credentials (ADC). 
- **Zero Secrets:** There are **NO API keys** and **NO Secret Manager keys** required or permitted in this repository. 
- **Cost Protection:** The Cloud Run deployment explicitly requires the `--no-allow-unauthenticated` flag. The service cannot be invoked by the public internet, completely preventing runaway billing and quota exhaustion.

## Quickstart

### Local Installation
```bash
# Clone the repository
git clone https://github.com/your-username/paper-to-deck.git
cd paper-to-deck

# Authenticate with Google Cloud (Vertex AI)
gcloud auth application-default login

# Configure your environment
cp .env.example .env
# Edit .env and ensure GOOGLE_CLOUD_PROJECT is set to your-project-id

# Install dependencies using uv
uv sync

# Run the local server
PAPER_TO_DECK_SANDBOX=/tmp/p2d uv run uvicorn paper_to_deck.web.app:app --reload
```

### Google Cloud Run Deployment
To deploy to Google Cloud Run, execute the following command. The `--no-allow-unauthenticated` flag is required to protect your GCP quota.

```bash
gcloud run deploy paper-to-deck \
  --source . \
  --region us-central1 \
  --project your-project-id \
  --no-allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash
```
