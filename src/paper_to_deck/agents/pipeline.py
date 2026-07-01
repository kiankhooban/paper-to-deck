from __future__ import annotations

import os

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from .tools import render_deck_tool

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


import sys
from pathlib import Path

def _vision_crop_toolset() -> McpToolset:
    src_path = str(Path(__file__).parent.parent.parent)
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[
                    "-c",
                    f"import sys; sys.path.insert(0, {repr(src_path)}); import runpy; runpy.run_module('paper_to_deck.mcp_server', run_name='__main__')"
                ],
                env=os.environ.copy()
            ),
            timeout=600.0
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
            "the paper text and figure manifest. Produce EXACTLY the number of main slides specified "
            "in the 'slides' key of {constraints}. Move all heavy derivations and secondary results "
            "into appendix slides (section='appendix', up to 20). Output a DeckOutline JSON: "
            "{title, theme, font, slides:[{title, bullets, notes, image_id, section}]}. "
            "The 'section' field MUST be exactly \"main\" or \"appendix\" (no other values allowed). "
            "Set 'theme' and 'font' exactly to the values given in {constraints}. Leave image_id null. "
            "- Map the flow precisely to the 10+20 structure.\n"
            "- CRITICAL: DO NOT use markdown formatting (like **stars** for bold or * for italic). Output plain text only.\n"
            "- CRITICAL: DO NOT use LaTeX formatting for mathematical expressions (e.g. no $ or \\). Use plain unicode math symbols (e.g. E=mc², α, ×, ≤) instead.\n"
            "- The `section` field MUST be exactly \"main\" or \"appendix\"."
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
            "manifest. The 'section' field MUST remain exactly \"main\" or \"appendix\". Output the updated DeckOutline JSON."
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
