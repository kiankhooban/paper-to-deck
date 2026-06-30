from __future__ import annotations

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
    message = (
        f"Constraints are already decided: minutes={constraints['minutes']}, "
        f"audience={constraints['audience']}, focus={constraints['focus']}, "
        f"want_flowcharts={constraints['want_flowcharts']}. Do not ask me anything. "
        f"Call parse_paper with this exact pdf_path: {pdf_path}. "
        f"Then build and render the full deck."
    )
    content = Content(parts=[Part(text=message)])
    async for _event in runner.run_async(user_id="web", session_id="web", new_message=content):
        pass
    return f"{os.environ['PAPER_TO_DECK_SANDBOX']}/deck.html"
