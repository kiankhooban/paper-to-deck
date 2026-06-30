FROM python:3.11-slim

RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN uv pip install --system .

ENV PAPER_TO_DECK_SANDBOX=/tmp/paper_to_deck_sandbox
ENV GEMINI_MODEL=gemini-2.5-flash
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION are injected at deploy time; no api key.
RUN mkdir -p /tmp/paper_to_deck_sandbox/assets

ENV PORT=8080
EXPOSE 8080
# The FastAPI app runs the pipeline and serves the custom UI
CMD ["sh", "-c", "uvicorn paper_to_deck.web.app:app --host 0.0.0.0 --port ${PORT}"]
