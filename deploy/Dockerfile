FROM python:3.11-slim

RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN uv pip install --system .

ENV PAPER_TO_DECK_SANDBOX=/tmp/paper_to_deck_sandbox
ENV GEMINI_MODEL=gemini-1.5-flash
RUN mkdir -p /tmp/paper_to_deck_sandbox/assets

ENV PORT=8080
EXPOSE 8080
# ADK serves the agent API; the agent module is paper_to_deck.agents.pipeline:root_agent
CMD ["sh", "-c", "adk api_server --host 0.0.0.0 --port ${PORT} src/paper_to_deck/agents"]
