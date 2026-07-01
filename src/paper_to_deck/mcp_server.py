from __future__ import annotations

"""Model Context Protocol (MCP) server for Vision and Cropping.

Exposes a standard MCP stdio tool that the ADK pipeline calls to parse 
and extract figures from PDFs.
"""

import os
from typing import Any

import anyio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from .pdf_parser import parse_paper

_TOOL_NAME = "parse_paper"


def _sandbox_root() -> str:
    root = os.environ.get("PAPER_TO_DECK_SANDBOX")
    if not root:
        raise RuntimeError("PAPER_TO_DECK_SANDBOX is not set")
    return root


def _handle_parse_paper(pdf_path: str) -> str:
    paper = parse_paper(pdf_path, sandbox_root=_sandbox_root())
    return paper.model_dump_json()


def build_server() -> Server:
    server: Server = Server("paper-to-deck-vision-crop")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=_TOOL_NAME,
                description="Extract text and caption-matched figure crops from a PDF in the sandbox.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF inside the sandbox root.",
                        }
                    },
                    "required": ["pdf_path"],
                },
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        if name != _TOOL_NAME:
            raise ValueError(f"unknown tool: {name}")
        result = _handle_parse_paper(arguments["pdf_path"])
        return [types.TextContent(type="text", text=result)]

    return server


def main() -> None:
    server = build_server()

    async def _run() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    anyio.run(_run)


if __name__ == "__main__":
    main()
