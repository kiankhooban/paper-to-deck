# Paper-to-Deck Architect

Paper-to-Deck Architect is a multi-agent AI system built for the Kaggle 5-Day AI Agents Capstone. It autonomously ingests dense scientific and mathematical research papers (PDFs) and instantly distills them into a beautifully designed, 15-minute interactive presentation deck (Reveal.js).

## Features
- **Multi-Agent Orchestration**: Built using Google ADK and powered by Gemini 2.5 Flash, the system utilizes a specialized pipeline of agents (`Concierge`, `Distiller`, `Visual Matcher`, and `Frontend Coder`) to parse and structure the paper seamlessly.
- **Vision-Powered MCP Server**: Employs an internal Model Context Protocol (MCP) server running PyMuPDF to extract exact visual crops of scientific figures and tables, mapping them logically to the correct slides via caption matching.
- **Dynamic AI Slide Estimation**: Contains a Fast LLM endpoint to calculate the perfect talk duration and number of slides based on the density of the paper, audience type, and core focus.
- **Hidden Appendix Pattern**: Keeps the presentation strictly within its time limit by routing heavy mathematical derivations and secondary graphs into a "Hidden Appendix", available out of the linear flow for Q&A sessions.
- **Flawless Formatting**: 
  - LaTeX mathematical equations are translated to clean, robust unicode expressions.
  - Strict Pydantic `Literal` schemas enforce exact styling, ensuring 0% hallucination of UI themes.
  - XSS-safe and path-traversal secure.
- **PDF Export**: Single-click printing to high-fidelity PDF formats right from the slide viewer.

## Architecture Highlights
The runtime is isolated to Google Cloud. The PDF inputs and extracted assets are strongly sandboxed to prevent path traversal. 
- **Agents:** Google ADK (Agent Development Kit) 
- **Intelligence:** Gemini 2.5 Flash (via Vertex AI)
- **Frontend / Backend:** FastAPI, Reveal.js
- **Tooling Interface:** Model Context Protocol (MCP) Server for PyMuPDF

## Security & Deployment
This project is secured by default. It employs **Google Cloud Vertex AI with Application Default Credentials (ADC)**. 
- There are NO hardcoded API keys. 
- Do NOT add a `GOOGLE_API_KEY` to the `.env` file. 
- The Cloud Run deployment is strictly authenticated, preventing internet-wide execution and runaway billing.

### Local Installation
```bash
# Clone the repository
git clone https://github.com/your-username/paper-to-deck.git
cd paper-to-deck

# Authenticate with Google Cloud (Vertex AI)
gcloud auth application-default login

# Configure your environment
cp .env.example .env
# Edit .env and set GOOGLE_CLOUD_PROJECT to your project ID

# Install dependencies using uv
uv sync

# Run the local server
PAPER_TO_DECK_SANDBOX=/tmp/p2d uv run uvicorn paper_to_deck.web.app:app --reload
```

### Google Cloud Run Deployment
To deploy to Google Cloud Run, execute the following command. Note that `--no-allow-unauthenticated` is highly recommended to protect your quota.

```bash
gcloud run deploy paper-to-deck \
  --source . \
  --region us-central1 \
  --project your-project-id \
  --no-allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash
```
