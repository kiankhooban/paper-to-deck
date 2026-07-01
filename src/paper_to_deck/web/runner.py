from __future__ import annotations

"""Bridges the FastAPI web layer with the ADK agent pipeline.

Starts the ADK execution session for an uploaded paper.
"""

import os

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from ..agents.pipeline import build_root_agent


async def run_pipeline(pdf_path: str, constraints: dict) -> str:
    """Run the ADK pipeline with form-supplied constraints; return the deck.html path.

    The constraints form replaces the chat interview, so the message hands the
    concierge its answers directly instead of making it ask.
    """
    agent = build_root_agent()
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="paper_to_deck", session_service=session_service)
    await session_service.create_session(app_name="paper_to_deck", user_id="web", session_id="web")
    import json
    constraints_json = json.dumps(constraints)
    message = (
        f"Constraints are already decided:\n{constraints_json}\n\n"
        "You MUST output exactly this JSON object. Do not add any text before or after.\n"
        f"Also note for the next agent: the user-provided pdf_path is {pdf_path}"
    )
    content = Content(parts=[Part(text=message)])
    async for event in runner.run_async(user_id="web", session_id="web", new_message=content):
        print(f"ADK EVENT: {event}", flush=True)
    return f"{os.environ['PAPER_TO_DECK_SANDBOX']}/deck.html"
