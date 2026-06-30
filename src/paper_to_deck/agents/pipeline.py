from __future__ import annotations

import os

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from .tools import render_deck_tool

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


def _vision_crop_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python",
                args=["-m", "paper_to_deck.mcp_server"],
            )
        ),
        tool_filter=["parse_paper"],
    )


def build_root_agent() -> SequentialAgent:
    concierge = LlmAgent(
        name="concierge",
        model=MODEL,
        instruction=(
            "You interview the user to set deck constraints. Ask for: talk length "
            "(default 15 minutes), target audience, the single core focus of the talk, "
            "and whether they want AI-generated flowchart visuals. Output a compact JSON "
            "object with keys: minutes, audience, focus, want_flowcharts."
        ),
        output_key="constraints",
    )

    distiller = LlmAgent(
        name="distiller",
        model=MODEL,
        instruction=(
            "You read a research paper and write a strict slide outline honoring "
            "{constraints}. Call the parse_paper tool with the user-provided pdf_path to get "
            "the paper text and figure manifest. Produce EXACTLY 10 main slides and up to 20 "
            "appendix slides. Move all heavy derivations and secondary results into appendix "
            "slides (section='appendix'). Output a DeckOutline JSON: "
            "{title, slides:[{title, bullets, notes, image_id, section}]}. Leave image_id null."
        ),
        tools=[_vision_crop_toolset()],
        output_key="deck_outline",
    )

    visual_matcher = LlmAgent(
        name="visual_matcher",
        model=MODEL,
        instruction=(
            "Given the outline in {deck_outline} and the figure manifest already returned by "
            "parse_paper, decide which figure (by its image_path, e.g. 'assets/fig_1.png') best "
            "supports each slide based on the captions. Set each slide's image_id to that path, "
            "or null if no figure fits. Do not invent paths: only use image_path values from the "
            "manifest. Output the updated DeckOutline JSON."
        ),
        output_key="mapped_outline",
    )

    frontend_coder = LlmAgent(
        name="frontend_coder",
        model=MODEL,
        instruction=(
            "Take the final outline in {mapped_outline} and call render_deck_tool with that "
            "exact JSON string. Do not write HTML yourself. Report the returned deck path to "
            "the user."
        ),
        tools=[FunctionTool(render_deck_tool)],
        output_key="deck_path",
    )

    return SequentialAgent(
        name="paper_to_deck_architect",
        sub_agents=[concierge, distiller, visual_matcher, frontend_coder],
    )


root_agent = build_root_agent()
